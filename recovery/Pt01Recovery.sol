// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

/// @notice Narrow, temporary PT-01 recovery implementation for the Exchange proxy.
/// @dev All ordinary calls delegate to the exact live Exchange implementation,
///      0x0a44049dbbb6b4762a6ba37aa0f7548c0b4a3723 (23,959 runtime bytes, sha256
///      fc7374f3969381160732fe98c5e3145e00c3f167f168d61d65bb4972e9a6b268). That
///      implementation was installed by the 2026-10-20 governance batch; the older
///      0x0f3febfc94876b0c895f7acecdc8f5c863b549ee is no longer the proxy target.
///      The live dispatcher exposes exactly four sweep-family mutators - sweep(address),
///      requestSweep(address), finalizeSweep(address) and
///      reconcileSweepCredit(address,uint256) - and no pending-sweep clear route, so the
///      fallback blocks those four for an affected user while recovery is active.
///      Deployment and upgrade require separate review and governance approval.
contract Pt01Recovery {
    address private constant LIVE_IMPLEMENTATION = address(uint160(uint256(0x000a44049dbbb6b4762a6ba37aa0f7548c0b4a3723)));
    address private constant TIMELOCK = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address private constant FIRST_USER = address(uint160(uint256(0x0056cbe78a5cdfa10147927aec550aa7f2fb3d3d01)));
    address private constant SECOND_USER = address(uint160(uint256(0x009c8599c32224d7d9956a7def18f7314162f77baf)));
    address private constant FIRST_PROXY = address(uint160(uint256(0x001e8a704179cc6221592c362daa52a341ae20084d)));
    address private constant SECOND_PROXY = address(uint160(uint256(0x00f6b60cdf359af5538495831a9f2bbcada23e10e6)));
    address private constant SPOT_BALANCE_PRECOMPILE = address(0x801);

    bytes4 private constant SWEEP = 0x01681a62;
    bytes4 private constant REQUEST_SWEEP = 0xe0189108;
    bytes4 private constant FINALIZE_SWEEP = 0x6d142da1;
    bytes4 private constant RECONCILE_SWEEP_CREDIT = 0x6a3214c9;
    bytes32 private constant ACTIVE_SLOT = bytes32(uint256(keccak256("papertrade.pt01.rescue.active.v1")) - 1);
    uint64 private constant FEE_RESERVE = 100_000_000; // 1 USDC in HyperCore raw units.
    uint64 private constant FIRST_SPOT = 5_005_091_600;
    uint64 private constant SECOND_SPOT = 1_210_000_000;

    event RecoveryQueued(address indexed user, address indexed proxy, uint64 amount, uint32 blockNumber);
    event RecoveryResidualQueued(address indexed user, address indexed proxy, uint32 blockNumber);
    event RecoveryFinalized(address indexed user, uint64 credited);

    modifier onlyTimelock() {
        require(msg.sender == TIMELOCK, "PT01: timelock only");
        _;
    }

    function rescueEnqueue(address user) external onlyTimelock {
        (address proxy, uint64 balance, uint256 mask) = _case(user);
        require(_active() & (mask | (mask << 2)) == 0, "PT01: already active");
        require(_spotBalance(proxy) == balance, "PT01: balance changed");

        bytes32 pendingSlot = keccak256(abi.encode(user, uint256(33)));
        uint256 pending = _load(pendingSlot);
        require(uint64(pending) == balance && uint64(pending >> 64) == 0, "PT01: pending changed");
        require(uint32(pending >> 128) != 0 && pending >> 160 == 0, "PT01: pending format");
        bytes32 lastSlot = keccak256(abi.encode(proxy, uint256(32)));
        require(_load(lastSlot) != block.number, "PT01: swept this block");
        require(block.number <= type(uint32).max, "PT01: block overflow");

        uint64 amount = balance - FEE_RESERVE;
        _store(ACTIVE_SLOT, _active() | mask);
        _store(pendingSlot, uint256(amount) | (block.number << 128));
        _store(lastSlot, block.number);
        IRescueDepositProxy(proxy).sweepAllToExchange(0, amount, 0);
        emit RecoveryQueued(user, proxy, amount, uint32(block.number));
    }

    /// @dev Use only after the first reduced send is independently confirmed
    ///      delivered with no fee and exactly 1 USDC left in the user proxy.
    function rescueEnqueueResidual(address user) external onlyTimelock {
        (address proxy, uint64 balance, uint256 mask) = _case(user);
        require(_active() & mask != 0 && _active() & (mask << 2) == 0, "PT01: wrong phase");
        require(_spotBalance(proxy) == FEE_RESERVE, "PT01: residual changed");

        bytes32 pendingSlot = keccak256(abi.encode(user, uint256(33)));
        uint256 pending = _load(pendingSlot);
        require(uint64(pending) == balance - FEE_RESERVE && uint64(pending >> 64) == 0, "PT01: pending changed");
        require(uint32(pending >> 128) < block.number && pending >> 160 == 0, "PT01: wait a block");
        bytes32 lastSlot = keccak256(abi.encode(proxy, uint256(32)));
        require(_load(lastSlot) != block.number, "PT01: swept this block");
        require(block.number <= type(uint32).max, "PT01: block overflow");

        _store(ACTIVE_SLOT, _active() | (mask << 2));
        _store(pendingSlot, uint256(FEE_RESERVE) | (block.number << 128));
        _store(lastSlot, block.number);
        IRescueDepositProxy(proxy).sweepAllToExchange(0, FEE_RESERVE, 0);
        emit RecoveryResidualQueued(user, proxy, uint32(block.number));
    }

    /// @dev The operator must first confirm the exact proxy-to-Exchange Core transfer
    ///      in both public ledgers and the Core execution record after finality.
    function rescueFinalize(address user) external onlyTimelock {
        (address proxy, uint64 balance, uint256 mask) = _case(user);
        require(_active() & mask != 0, "PT01: not active");
        bool residualQueued = _active() & (mask << 2) != 0;
        uint64 credited = residualQueued ? balance : balance - FEE_RESERVE;
        uint64 pendingAmount = residualQueued ? FEE_RESERVE : credited;
        bytes32 pendingSlot = keccak256(abi.encode(user, uint256(33)));
        uint256 pending = _load(pendingSlot);
        require(uint64(pending) == pendingAmount && uint64(pending >> 64) == 0, "PT01: pending changed");
        require(uint32(pending >> 128) < block.number && pending >> 160 == 0, "PT01: wait a block");
        require(_spotBalance(proxy) == 0, "PT01: funds remain");

        bytes32 userBalanceSlot = keccak256(abi.encode(user, uint256(9)));
        uint256 userBefore = _load(userBalanceSlot);
        uint256 treasuryBefore = _load(bytes32(uint256(14)));
        uint256 totalsBefore = _load(bytes32(uint256(22)));

        _store(pendingSlot, 0);
        require(credited % 100 == 0, "PT01: unit mismatch");
        _reconcile(user, credited);
        require(_load(pendingSlot) == 0, "PT01: finalization mismatch");
        uint256 credit = uint256(credited) * 1e10;
        require(_load(userBalanceSlot) == userBefore + credit, "PT01: user credit mismatch");
        require(_load(bytes32(uint256(14))) == treasuryBefore + credit, "PT01: treasury mismatch");
        require(_load(bytes32(uint256(22))) == totalsBefore + credit, "PT01: total mismatch");

        _store(ACTIVE_SLOT, _active() & ~(mask | (mask << 2)));
        emit RecoveryFinalized(user, credited);
    }

    fallback() external payable {
        if (msg.data.length >= 36 && (msg.sig == SWEEP || msg.sig == REQUEST_SWEEP || msg.sig == FINALIZE_SWEEP || msg.sig == RECONCILE_SWEEP_CREDIT)) {
            bytes32 rawUser;
            assembly { rawUser := calldataload(4) }
            if (rawUser == bytes32(uint256(uint160(FIRST_USER))) && _active() & 1 != 0) revert("PT01: recovery active");
            if (rawUser == bytes32(uint256(uint160(SECOND_USER))) && _active() & 2 != 0) revert("PT01: recovery active");
        }
        address live = LIVE_IMPLEMENTATION;
        assembly {
            calldatacopy(0, 0, calldatasize())
            let ok := delegatecall(gas(), live, 0, calldatasize(), 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch ok
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }

    receive() external payable {
        address live = LIVE_IMPLEMENTATION;
        assembly {
            let ok := delegatecall(gas(), live, 0, 0, 0, 0)
            returndatacopy(0, 0, returndatasize())
            switch ok
            case 0 { revert(0, returndatasize()) }
            default { return(0, returndatasize()) }
        }
    }

    function _case(address user) private pure returns (address proxy, uint64 balance, uint256 mask) {
        if (user == FIRST_USER) return (FIRST_PROXY, FIRST_SPOT, 1);
        if (user == SECOND_USER) return (SECOND_PROXY, SECOND_SPOT, 2);
        revert("PT01: unknown user");
    }

    function _reconcile(address user, uint64 credited) private {
        (bool ok, bytes memory result) = LIVE_IMPLEMENTATION.delegatecall(
            abi.encodeWithSelector(RECONCILE_SWEEP_CREDIT, user, uint256(credited) / 100)
        );
        if (!ok) assembly { revert(add(result, 32), mload(result)) }
        require(result.length == 0, "PT01: reconciliation result");
    }

    function _spotBalance(address proxy) private view returns (uint64 spot) {
        (bool ok, bytes memory output) = SPOT_BALANCE_PRECOMPILE.staticcall(abi.encode(proxy, uint64(0)));
        require(ok && output.length == 96, "PT01: Core read failed");
        (uint256 raw,,) = abi.decode(output, (uint256, uint256, uint256));
        require(raw <= type(uint64).max, "PT01: Core balance overflow");
        return uint64(raw);
    }

    function _active() private view returns (uint256 active) {
        bytes32 slot = ACTIVE_SLOT;
        assembly { active := sload(slot) }
    }

    function _load(bytes32 slot) private view returns (uint256 value) {
        assembly { value := sload(slot) }
    }

    function _store(bytes32 slot, uint256 value) private {
        assembly { sstore(slot, value) }
    }
}

interface IRescueDepositProxy {
    function sweepAllToExchange(uint64 tokenId, uint64 spotAmount, uint64 perpAmount) external;
}