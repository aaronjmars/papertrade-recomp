// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function warp(uint256) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}

contract SelectorGapLocalTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));

    bytes32 constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant ADMIN_SLOT = 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103;
    bytes32 constant TRANSFER_TOPIC = 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef;
    bytes32 constant MINTER_TOPIC = 0xad0f299ec81a386c98df0ac27dae11dd020ed1b56963c53a7292e7a3a314539a;
    bytes32 constant OWNER_TOPIC = 0x4ffd725fc4a22075e9ec71c59edf9c38cdeb588a91b24fc5b61388c5be41282b;
    bytes32 constant DEPLOYER_TOPIC = 0x09bdaf5fdab1e55bea2219aeaa3c7334e422f842e1fb25dc319e8a2b3d5e0167;
    bytes32 constant CALLER_TOPIC = 0xfe60173cc964bc674632fcf67031bba24c8a99a4a7d6518c726586978b7e30d3;
    bytes32 constant MINT_PARAMS_TOPIC = 0xdbf6f1878073adede0b153c63f457c1c601a056124755086092f973f19550176;
    bytes32 constant MIN_DELAY_TOPIC = 0x25cd0ae91e995bc58ea33869249d0bcf40f2b2c8331ec976c96096bf7d27f464;
    bytes32 constant OP_SCHEDULED_TOPIC = 0x78f3bc93d9f0e2beb7fc8fe3192b142c5e70b8813403674aff3f81fc83af5b39;
    bytes32 constant BATCH_SCHEDULED_TOPIC = 0x0b9c64b5b18792c995334aa1e837673c5a9cdb8f004ab10fb652f4eecb8d551f;
    bytes32 constant OP_EXECUTED_TOPIC = 0x2a08801cf3674ab09756ae78a3a4833813465af6af958136b360eab6b71c8952;
    bytes32 constant BATCH_EXECUTED_TOPIC = 0xaa1510acf32db51981a900a90589bafbf6f442c657a0b916fd3afe22c1474bcd;
    bytes32 constant OP_CANCELLED_TOPIC = 0xcf0f63b97f3387253cbc0bde884f975df77e39184dc3280c2c81be495f58eef4;

    address constant TIMELOCK = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    address constant FACTORY_PROXY = address(uint160(uint256(0x001629b7d46bef6e13ff754174fc9f32dea309b38f)));
    address constant SESSION_PROXY = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant PAPER_PROXY = address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e)));
    address constant TOKENOMICS_PROXY = address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9)));
    address constant PROXY_ADMIN = address(uint160(uint256(0x00e79c91cc682f1bb401a9cab74c900470190f0f8f)));
    address constant FACTORY_IMPL = address(uint160(uint256(0x008f22a73a23a2de0dbfdf6729f4d8c07dbdc69cf0)));
    address constant SESSION_IMPL = address(uint160(uint256(0x008a5069fe303e8f81e91825436e956d595032e558)));
    address constant PAPER_IMPL = address(uint160(uint256(0x00433bd418ec92818a960585f4d5fae563e735bb4a)));
    address constant TOKENOMICS_IMPL = address(uint160(uint256(0x00600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f)));
    address constant FACTORY_FRESH = address(uint160(uint256(0x00000000000000000000000000000000000000feed)));
    address constant BATCH_PROXY = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant BATCH_IMPL = address(uint160(uint256(0x00e0bc9cc7b067060aafccbaa3e250700c9cdd7262)));
    address constant OUTSIDER = address(uint160(uint256(0x00000000000000000000000000000000000000beef)));
    address constant HOLDER = address(uint160(uint256(0x00000000000000000000000000000000000000cafe)));
    address constant NEW_VALUE = address(uint160(uint256(0x000000000000000000000000000000000000001234)));
    address constant DEPLOYER_PINNED = address(uint160(uint256(0x00df1bda875c9393a663ce69bf6a7fbaa73dfd053d)));
    address constant TIMELOCK_OWNER = address(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)));

    uint256 constant MINT_X = 2 * 10 ** 24;
    uint256 constant MINT_Y = 10 * 10 ** 24;
    uint256 constant MINT_RATE = 100 * 10 ** 18;
    uint256 constant MINT_SCALE = 120 * 10 ** 24;
    uint256 constant MIN_DELAY = 604800;

    function setUp() public {
        bytes memory proxyRuntime = vm.parseBytes(vm.readFile("runtime/SharedProxy.hex"));
        bytes memory paperProxyRuntime = vm.parseBytes(vm.readFile("runtime/PaperProxy.hex"));
        vm.etch(FACTORY_PROXY, proxyRuntime);
        vm.etch(SESSION_PROXY, proxyRuntime);
        vm.etch(TOKENOMICS_PROXY, proxyRuntime);
        vm.etch(FACTORY_FRESH, proxyRuntime);
        vm.etch(PAPER_PROXY, paperProxyRuntime);
        vm.etch(FACTORY_IMPL, vm.parseBytes(vm.readFile("runtime/FactoryImplementation.hex")));
        vm.etch(SESSION_IMPL, vm.parseBytes(vm.readFile("runtime/SessionImplementation.hex")));
        vm.etch(PAPER_IMPL, vm.parseBytes(vm.readFile("runtime/PaperImplementation.hex")));
        vm.etch(TOKENOMICS_IMPL, vm.parseBytes(vm.readFile("runtime/TokenomicsImplementation.hex")));
        vm.etch(TIMELOCK, vm.parseBytes(vm.readFile("runtime/Timelock.hex")));
        vm.etch(BATCH_PROXY, proxyRuntime);
        vm.etch(BATCH_IMPL, vm.parseBytes(vm.readFile("runtime/BatchImplementation.hex")));
        vm.etch(PROXY_ADMIN, vm.parseBytes(vm.readFile("runtime/ProxyAdmin.hex")));
        vm.etch(BATCH_PROXY, proxyRuntime);
        vm.etch(BATCH_IMPL, vm.parseBytes(vm.readFile("runtime/BatchImplementation.hex")));
        vm.etch(PROXY_ADMIN, vm.parseBytes(vm.readFile("runtime/ProxyAdmin.hex")));

        vm.store(BATCH_PROXY, IMPL_SLOT, bytes32(uint256(uint160(BATCH_IMPL))));
        vm.store(BATCH_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(PROXY_ADMIN))));
        vm.store(PROXY_ADMIN, bytes32(uint256(0)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(BATCH_PROXY, IMPL_SLOT, bytes32(uint256(uint160(BATCH_IMPL))));
        vm.store(BATCH_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(PROXY_ADMIN))));
        vm.store(PROXY_ADMIN, bytes32(uint256(0)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(FACTORY_PROXY, IMPL_SLOT, bytes32(uint256(uint160(FACTORY_IMPL))));
        vm.store(FACTORY_FRESH, IMPL_SLOT, bytes32(uint256(uint160(FACTORY_IMPL))));
        vm.store(SESSION_PROXY, IMPL_SLOT, bytes32(uint256(uint160(SESSION_IMPL))));
        vm.store(PAPER_PROXY, IMPL_SLOT, bytes32(uint256(uint160(PAPER_IMPL))));
        vm.store(TOKENOMICS_PROXY, IMPL_SLOT, bytes32(uint256(uint160(TOKENOMICS_IMPL))));
        vm.store(FACTORY_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(PROXY_ADMIN))));
        vm.store(FACTORY_FRESH, ADMIN_SLOT, bytes32(uint256(uint160(PROXY_ADMIN))));
        vm.store(FACTORY_FRESH, bytes32(uint256(0)), bytes32(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2) << 16));
        vm.store(SESSION_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(PROXY_ADMIN))));
        vm.store(PAPER_PROXY, ADMIN_SLOT, bytes32(uint256(uint160(PROXY_ADMIN))));

        // Pinned factory state: owner slot 3, authorized deployer slot 4.
        vm.store(FACTORY_PROXY, bytes32(uint256(3)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(FACTORY_PROXY, bytes32(uint256(4)), bytes32(uint256(uint160(DEPLOYER_PINNED))));
        // Pinned SessionKeyManager state: slot 2 owner, slot 3 authorized Exchange caller.
        vm.store(SESSION_PROXY, bytes32(uint256(0)), bytes32(uint256(1)));
        vm.store(SESSION_PROXY, bytes32(uint256(1)), bytes32(uint256(0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77)));
        vm.store(SESSION_PROXY, bytes32(uint256(2)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(SESSION_PROXY, bytes32(uint256(3)), bytes32(uint256(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)))));
        // Pinned PAPER token state.
        vm.store(PAPER_PROXY, bytes32(uint256(3)), bytes32(uint256(uint160(TIMELOCK))));
        vm.store(PAPER_PROXY, bytes32(uint256(4)), bytes32(uint256(uint160(TOKENOMICS_PROXY))));
        vm.store(PAPER_PROXY, bytes32(uint256(6)), bytes32(uint256(1000 ether)));
        vm.store(PAPER_PROXY, keccak256(abi.encode(HOLDER, uint256(7))), bytes32(uint256(500 ether)));
        // Pinned Tokenomics state: packed owner/initialized word in slot 0.
        vm.store(TOKENOMICS_PROXY, bytes32(uint256(0)), bytes32((uint256(uint160(TIMELOCK_OWNER)) << 16) | 1));
        vm.store(TOKENOMICS_PROXY, bytes32(uint256(1)), bytes32(uint256(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)))));
        vm.store(TOKENOMICS_PROXY, bytes32(uint256(5)), bytes32(MINT_X));
        vm.store(TOKENOMICS_PROXY, bytes32(uint256(6)), bytes32(uint256(5) * 10 ** 24));
        vm.store(TOKENOMICS_PROXY, bytes32(uint256(7)), bytes32(MINT_RATE));
        vm.store(TOKENOMICS_PROXY, bytes32(uint256(8)), bytes32(MINT_SCALE));
        // Pinned timelock state: slot 0 owner, slot 1 minimum delay.
        vm.store(TIMELOCK, bytes32(uint256(0)), bytes32(uint256(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)))));
        vm.store(TIMELOCK, bytes32(uint256(1)), bytes32(MIN_DELAY));
    }

    function callAs(address caller, address target, bytes memory data) internal returns (bool, bytes memory) {
        vm.prank(caller);
        return target.call(data);
    }

    function expectRevertSelector(address caller, address target, bytes memory data, bytes4 want) internal {
        (bool ok, bytes memory out) = callAs(caller, target, data);
        require(!ok, "expected revert");
        require(out.length == 4, "expected 4-byte revert payload");
        require(bytes4(out) == want, "unexpected revert selector");
    }

    function checkRevertSelector(address target, bytes memory data, bytes4 want) internal view {
        (bool ok, bytes memory out) = target.staticcall(data);
        require(!ok && out.length == 4 && bytes4(out) == want, "unexpected selector");
    }

    function onlyLog(Vm.Log[] memory logs, address emitter, bytes32 topic) internal pure returns (Vm.Log memory) {
        require(logs.length == 1, "unexpected log count");
        require(logs[0].emitter == emitter && logs[0].topics[0] == topic, "unexpected log");
        return logs[0];
    }

    function topicAddress(address who) internal pure returns (bytes32) {
        return bytes32(uint256(uint160(who)));
    }

    // ---------------------------------------------------------------- PAPER token

    function testPaperBurnFromMinter() public {
        uint256 supplyBefore = uint256(vm.load(PAPER_PROXY, bytes32(uint256(6))));
        bytes32 balanceSlot = keccak256(abi.encode(HOLDER, uint256(7)));
        uint256 balanceBefore = uint256(vm.load(PAPER_PROXY, balanceSlot));
        vm.recordLogs();
        (bool ok,) = callAs(TOKENOMICS_PROXY, PAPER_PROXY,
                            abi.encodeWithSelector(bytes4(0x9dc29fac), HOLDER, uint256(10 ether)));
        require(ok, "minter burn failed");
        Vm.Log memory log = onlyLog(vm.getRecordedLogs(), PAPER_PROXY, TRANSFER_TOPIC);
        require(uint256(vm.load(PAPER_PROXY, bytes32(uint256(6)))) == supplyBefore - 10 ether, "supply not reduced");
        require(uint256(vm.load(PAPER_PROXY, balanceSlot)) == balanceBefore - 10 ether, "balance not reduced");
        require(log.topics[1] == topicAddress(HOLDER) && log.topics[2] == bytes32(0), "wrong transfer parties");
        require(abi.decode(log.data, (uint256)) == 10 ether, "wrong transfer amount");
        require(vm.load(PAPER_PROXY, bytes32(uint256(3))) == topicAddress(TIMELOCK), "owner slot changed");
        require(vm.load(PAPER_PROXY, bytes32(uint256(4))) == topicAddress(TOKENOMICS_PROXY), "minter slot changed");
    }

    function testPaperBurnRejections() public {
        bytes32 balanceSlot = keccak256(abi.encode(HOLDER, uint256(7)));
        uint256 supplyBefore = uint256(vm.load(PAPER_PROXY, bytes32(uint256(6))));
        expectRevertSelector(TIMELOCK, PAPER_PROXY,
                             abi.encodeWithSelector(bytes4(0x9dc29fac), HOLDER, uint256(1)),
                             bytes4(0xf8d2906c));
        expectRevertSelector(TOKENOMICS_PROXY, PAPER_PROXY,
                             abi.encodeWithSelector(bytes4(0x9dc29fac), HOLDER, uint256(501 ether)),
                             bytes4(0xf4d678b8));
        require(uint256(vm.load(PAPER_PROXY, bytes32(uint256(6)))) == supplyBefore, "supply changed on revert");
        require(uint256(vm.load(PAPER_PROXY, balanceSlot)) == 500 ether, "balance changed on revert");
    }

    function testPaperSetMinter() public {
        expectRevertSelector(OUTSIDER, PAPER_PROXY,
                             abi.encodeWithSelector(bytes4(0xfca3b5aa), NEW_VALUE), bytes4(0x30cd7471));
        require(vm.load(PAPER_PROXY, bytes32(uint256(4))) == bytes32(uint256(uint160(TOKENOMICS_PROXY))), "minter changed on revert");
        vm.recordLogs();
        (bool ok,) = callAs(TIMELOCK, PAPER_PROXY, abi.encodeWithSelector(bytes4(0xfca3b5aa), NEW_VALUE));
        require(ok, "owner setMinter failed");
        Vm.Log memory log = onlyLog(vm.getRecordedLogs(), PAPER_PROXY, MINTER_TOPIC);
        require(uint256(vm.load(PAPER_PROXY, bytes32(uint256(4)))) == uint256(uint160(NEW_VALUE)), "slot 4 not updated");
        require(log.topics.length == 2 && log.topics[1] == topicAddress(NEW_VALUE), "wrong minter event");
        require(log.data.length == 0, "unexpected event data");
        require(vm.load(PAPER_PROXY, bytes32(uint256(3))) == topicAddress(TIMELOCK), "owner slot changed");
        require(vm.load(PAPER_PROXY, bytes32(uint256(6))) == bytes32(uint256(1000 ether)), "supply changed");
    }

    // ------------------------------------------------------- SessionKeyManager

    function testSessionSetAuthorizedCaller() public {
        expectRevertSelector(OUTSIDER, SESSION_PROXY,
                             abi.encodeWithSelector(bytes4(0xcf8fbec9), NEW_VALUE), bytes4(0x30cd7471));
        require(vm.load(SESSION_PROXY, bytes32(uint256(3))) == topicAddress(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)))), "caller changed on revert");
        vm.recordLogs();
        (bool ok,) = callAs(TIMELOCK, SESSION_PROXY, abi.encodeWithSelector(bytes4(0xcf8fbec9), NEW_VALUE));
        require(ok, "owner setAuthorizedCaller failed");
        Vm.Log memory log = onlyLog(vm.getRecordedLogs(), SESSION_PROXY, CALLER_TOPIC);
        require(uint256(vm.load(SESSION_PROXY, bytes32(uint256(3)))) == uint256(uint160(NEW_VALUE)), "slot 3 not updated");
        require(log.topics.length == 2 && log.topics[1] == topicAddress(NEW_VALUE), "wrong caller event");
        require(vm.load(SESSION_PROXY, bytes32(uint256(0))) == bytes32(uint256(1)), "slot 0 changed");
        require(vm.load(SESSION_PROXY, bytes32(uint256(1))) == bytes32(uint256(0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77)), "domain cache changed");
        require(vm.load(SESSION_PROXY, bytes32(uint256(2))) == topicAddress(TIMELOCK), "owner slot changed");
        require(vm.load(SESSION_PROXY, bytes32(uint256(4))) == bytes32(0), "slot 4 changed");
        require(vm.load(SESSION_PROXY, bytes32(uint256(5))) == bytes32(0), "slot 5 changed");
    }

    // ---------------------------------------------------- DepositProxyFactory

    function testFactorySetAuthorizedDeployer() public {
        expectRevertSelector(OUTSIDER, FACTORY_PROXY,
                             abi.encodeWithSelector(bytes4(0xc6f881bc), NEW_VALUE), bytes4(0x30cd7471));
        require(vm.load(FACTORY_PROXY, bytes32(uint256(4))) == bytes32(uint256(uint160(DEPLOYER_PINNED))), "deployer changed on revert");
        vm.recordLogs();
        (bool ok,) = callAs(TIMELOCK, FACTORY_PROXY, abi.encodeWithSelector(bytes4(0xc6f881bc), NEW_VALUE));
        require(ok, "owner setAuthorizedDeployer failed");
        Vm.Log memory log = onlyLog(vm.getRecordedLogs(), FACTORY_PROXY, DEPLOYER_TOPIC);
        require(uint256(vm.load(FACTORY_PROXY, bytes32(uint256(4)))) == uint256(uint160(NEW_VALUE)), "slot 4 not updated");
        require(uint256(vm.load(FACTORY_PROXY, bytes32(uint256(3)))) == uint256(uint160(TIMELOCK)), "owner slot changed");
        require(log.topics[1] == topicAddress(NEW_VALUE), "wrong deployer event");
    }

    function testFactoryAdminInitializer() public {
        (bool ok, bytes memory out) = callAs(OUTSIDER, FACTORY_FRESH,
                                             abi.encodeWithSelector(bytes4(0x0f71c8bc), NEW_VALUE, OUTSIDER));
        require(!ok && out.length == 4 && bytes4(out) == bytes4(0xc031a0df), "outsider bootstrap result");
        require(vm.load(FACTORY_FRESH, bytes32(uint256(3))) == bytes32(0), "outsider wrote owner");
        vm.recordLogs();
        (ok,) = callAs(PROXY_ADMIN, FACTORY_FRESH, abi.encodeWithSelector(bytes4(0x0f71c8bc), NEW_VALUE, OUTSIDER));
        require(ok, "admin bootstrap failed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 2, "expected two bootstrap events");
        require(logs[0].topics[0] == OWNER_TOPIC && logs[1].topics[0] == DEPLOYER_TOPIC, "wrong bootstrap event order");
        require(uint256(vm.load(FACTORY_FRESH, bytes32(uint256(3)))) == uint256(uint160(NEW_VALUE)), "owner not written");
        require(uint256(vm.load(FACTORY_FRESH, bytes32(uint256(4)))) == uint256(uint160(OUTSIDER)), "deployer not written");
        expectRevertSelector(PROXY_ADMIN, FACTORY_FRESH,
                             abi.encodeWithSelector(bytes4(0x0f71c8bc), NEW_VALUE, OUTSIDER), bytes4(0x3f733c4f));
        expectRevertSelector(PROXY_ADMIN, FACTORY_PROXY,
                             abi.encodeWithSelector(bytes4(0x0f71c8bc), NEW_VALUE, OUTSIDER), bytes4(0x3f733c4f));
    }

    // --------------------------------------------------------------- Tokenomics

    function testTokenomicsSetMintParams() public {
        expectRevertSelector(OUTSIDER, TOKENOMICS_PROXY,
                             abi.encodeWithSelector(bytes4(0x12baae3b), MINT_X, MINT_Y, MINT_RATE, MINT_SCALE),
                             bytes4(0x30cd7471));
        expectRevertSelector(TIMELOCK_OWNER, TOKENOMICS_PROXY,
                             abi.encodeWithSelector(bytes4(0x12baae3b), MINT_Y, MINT_X, MINT_RATE, MINT_SCALE),
                             bytes4(0xbad8ef95));
        expectRevertSelector(TIMELOCK_OWNER, TOKENOMICS_PROXY,
                             abi.encodeWithSelector(bytes4(0x12baae3b), uint256(0), MINT_Y, MINT_RATE, MINT_SCALE),
                             bytes4(0xbad8ef95));
        uint256[4] memory before = [uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(5)))),
                                    uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(6)))),
                                    uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(7)))),
                                    uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(8))))];
        require(before[0] == MINT_X && before[1] == uint256(5) * 10 ** 24 && before[2] == MINT_RATE && before[3] == MINT_SCALE, "pinned params");
        vm.recordLogs();
        (bool ok,) = callAs(TIMELOCK_OWNER, TOKENOMICS_PROXY,
                            abi.encodeWithSelector(bytes4(0x12baae3b), uint256(3 * 10 ** 24), uint256(4 * 10 ** 24), uint256(7), uint256(8)));
        require(ok, "owner setMintParams failed");
        Vm.Log memory log = onlyLog(vm.getRecordedLogs(), TOKENOMICS_PROXY, MINT_PARAMS_TOPIC);
        require(log.topics.length == 1, "params event should be unindexed");
        require(uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(5)))) == 3 * 10 ** 24, "slot 5");
        require(uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(6)))) == 4 * 10 ** 24, "slot 6");
        require(uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(7)))) == 7, "slot 7");
        require(uint256(vm.load(TOKENOMICS_PROXY, bytes32(uint256(8)))) == 8, "slot 8");
        require(vm.load(TOKENOMICS_PROXY, bytes32(uint256(1))) == topicAddress(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)))), "exchange slot changed");
        require(vm.load(TOKENOMICS_PROXY, bytes32(uint256(0))) == bytes32((uint256(uint160(TIMELOCK_OWNER)) << 16) | 1), "owner word changed");
        (uint256 w0, uint256 w1, uint256 w2, uint256 w3) = abi.decode(log.data, (uint256, uint256, uint256, uint256));
        require(w0 == 3 * 10 ** 24 && w1 == 4 * 10 ** 24 && w2 == 7 && w3 == 8, "event payload mismatch");
    }

    // ----------------------------------------------------------------- Timelock


    function headSized(bytes memory full, uint256 headWords) internal pure returns (bytes memory out) {
        require(full.length >= 4 + 32 * headWords, "short encoding");
        out = new bytes(4 + 32 * (headWords - 1));
        for (uint256 i; i < out.length; ++i) out[i] = full[i];
    }


    function testDecodeGuards() public {
        bytes[12] memory calls;
        uint256[12] memory heads;
        calls[0] = abi.encodeWithSelector(bytes4(0x9dc29fac), HOLDER, uint256(1 ether));
        heads[0] = 2;
        calls[1] = abi.encodeWithSelector(bytes4(0xfca3b5aa), NEW_VALUE);
        heads[1] = 1;
        calls[2] = abi.encodeWithSelector(bytes4(0x12baae3b), MINT_X, MINT_Y, MINT_RATE, MINT_SCALE);
        heads[2] = 4;
        calls[3] = abi.encodeWithSelector(bytes4(0x485cc955), TIMELOCK_OWNER, TOKENOMICS_PROXY);
        heads[3] = 2;
        calls[4] = abi.encodeWithSelector(bytes4(0xcf8fbec9), NEW_VALUE);
        heads[4] = 1;
        calls[5] = abi.encodeWithSelector(bytes4(0xc6f881bc), NEW_VALUE);
        heads[5] = 1;
        calls[6] = abi.encodeWithSelector(bytes4(0x0f71c8bc), NEW_VALUE, OUTSIDER);
        heads[6] = 2;
        calls[7] = abi.encodeWithSelector(bytes4(0x9ccae24e), TIMELOCK_OWNER, OUTSIDER, NEW_VALUE, HOLDER, TIMELOCK);
        heads[7] = 5;
        calls[8] = abi.encodeWithSelector(bytes4(0x99a88ec4), FACTORY_PROXY, NEW_VALUE);
        heads[8] = 2;
        calls[9] = abi.encodeWithSelector(bytes4(0x9623609d), FACTORY_PROXY, NEW_VALUE, bytes(""));
        heads[9] = 3;
        calls[10] = abi.encodeWithSelector(bytes4(0x88aa4c12), TIMELOCK, uint256(0), bytes(""), bytes32(0));
        heads[10] = 4;
        calls[11] = abi.encodeWithSelector(bytes4(0x8b07f62b), new address[](0), new uint256[](0), new bytes[](0), bytes32(0));
        heads[11] = 4;
        address[12] memory targets;
        targets[0] = PAPER_PROXY; targets[1] = PAPER_PROXY; targets[2] = TOKENOMICS_PROXY;
        targets[3] = TOKENOMICS_PROXY; targets[4] = SESSION_PROXY; targets[5] = FACTORY_PROXY;
        targets[6] = FACTORY_FRESH; targets[7] = BATCH_PROXY; targets[8] = PROXY_ADMIN;
        targets[9] = PROXY_ADMIN; targets[10] = TIMELOCK; targets[11] = TIMELOCK;
        for (uint256 i; i < 12; ++i) {
            bytes memory selectorOnly = new bytes(4);
            for (uint256 j; j < 4; ++j) selectorOnly[j] = calls[i][j];
            (bool ok, bytes memory out) = callAs(TIMELOCK_OWNER, targets[i], selectorOnly);
            require(!ok && out.length == 0, "selector-only call not rejected with empty data");
            (ok, out) = callAs(TIMELOCK_OWNER, targets[i], headSized(calls[i], heads[i]));
            require(!ok && out.length == 0, "short head call not rejected with empty data");
            (ok, out) = callAs(TIMELOCK_OWNER, targets[i], calls[i]);
            require(!(!ok && out.length == 0), "full encoding rejected by the decode guard");
        }
    }

    function testTimelockSelfGatedSetters() public {
        expectRevertSelector(TIMELOCK_OWNER, TIMELOCK,
                             abi.encodeWithSelector(bytes4(0x8a99d586), uint256(86400)), bytes4(0x29c3b7ee));
        expectRevertSelector(TIMELOCK_OWNER, TIMELOCK,
                             abi.encodeWithSelector(bytes4(0xf2fde38b), NEW_VALUE), bytes4(0x29c3b7ee));
        vm.recordLogs();
        (bool ok,) = callAs(TIMELOCK, TIMELOCK, abi.encodeWithSelector(bytes4(0x8a99d586), uint256(86400)));
        require(ok, "self updateMinDelay failed");
        Vm.Log memory log = onlyLog(vm.getRecordedLogs(), TIMELOCK, MIN_DELAY_TOPIC);
        require(uint256(vm.load(TIMELOCK, bytes32(uint256(1)))) == 86400, "minDelay slot 1");
        require(abi.decode(log.data, (uint256)) == 86400, "minDelay event payload");
        vm.recordLogs();
        (ok,) = callAs(TIMELOCK, TIMELOCK, abi.encodeWithSelector(bytes4(0xf2fde38b), NEW_VALUE));
        require(ok, "self transferOwnership failed");
        log = onlyLog(vm.getRecordedLogs(), TIMELOCK, OWNER_TOPIC);
        require(uint256(vm.load(TIMELOCK, bytes32(uint256(0)))) == uint256(uint160(NEW_VALUE)), "owner slot 0");
        require(log.topics[1] == topicAddress(NEW_VALUE), "owner event payload");
        vm.store(TIMELOCK, bytes32(uint256(0)), bytes32(uint256(uint160(uint256(0x00696292762fd5ac3677a45edbe54eaece4194d1f6)))));
        expectRevertSelector(TIMELOCK, TIMELOCK,
                             abi.encodeWithSelector(bytes4(0xf2fde38b), address(0)), bytes4(0x49e27cff));
    }


    function testTimelockScheduleSingleAndExecute() public {
        bytes memory payload = abi.encodeWithSelector(bytes4(0x8a99d586), uint256(400));
        bytes memory scheduleCall = abi.encodeWithSelector(bytes4(0xb0e58bc9), TIMELOCK, uint256(0), payload, bytes32(0));
        expectRevertSelector(OUTSIDER, TIMELOCK, scheduleCall, bytes4(0x30cd7471));
        expectRevertSelector(TIMELOCK_OWNER, TIMELOCK,
                             abi.encodeWithSelector(bytes4(0x88aa4c12), TIMELOCK, uint256(0), payload, bytes32(0)),
                             bytes4(0x27c0d610));
        vm.recordLogs();
        (bool ok,) = callAs(TIMELOCK_OWNER, TIMELOCK, scheduleCall);
        require(ok, "schedule failed");
        Vm.Log memory scheduled = onlyLog(vm.getRecordedLogs(), TIMELOCK, OP_SCHEDULED_TOPIC);
        require(scheduled.topics.length == 3 && scheduled.topics[2] == topicAddress(TIMELOCK), "scheduled event shape");
        bytes32 opId = scheduled.topics[1];
        bytes32 opSlot = keccak256(abi.encode(opId, uint256(2)));
        uint256 ready = uint256(vm.load(TIMELOCK, opSlot));
        require(ready == block.timestamp + MIN_DELAY, "unexpected ready timestamp");
        require(uint256(vm.load(TIMELOCK, bytes32(uint256(1)))) == MIN_DELAY, "minDelay changed early");
        bytes memory executeCall = abi.encodeWithSelector(bytes4(0x88aa4c12), TIMELOCK, uint256(0), payload, bytes32(0));
        expectRevertSelector(OUTSIDER, TIMELOCK, executeCall, bytes4(0x30cd7471));
        expectRevertSelector(TIMELOCK_OWNER, TIMELOCK, executeCall, bytes4(0xf800799b));
        vm.warp(ready + 1);
        vm.recordLogs();
        (ok,) = callAs(TIMELOCK_OWNER, TIMELOCK, executeCall);
        require(ok, "execute failed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 2, "execute log count");
        require(logs[0].topics[0] == MIN_DELAY_TOPIC, "child call did not run first");
        require(uint256(vm.load(TIMELOCK, bytes32(uint256(1)))) == 400, "child call effect missing");
        Vm.Log memory done = onlyLog(singleOpLog(logs, OP_EXECUTED_TOPIC), TIMELOCK, OP_EXECUTED_TOPIC);
        require(done.topics[1] == opId, "executed event id");
        require(uint256(vm.load(TIMELOCK, opSlot)) == 1, "operation not marked done");
    }

    function singleOpLog(Vm.Log[] memory logs, bytes32 topic) internal pure returns (Vm.Log[] memory found) {
        uint256 count;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics[0] == topic) ++count;
        }
        found = new Vm.Log[](count);
        count = 0;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics[0] == topic) found[count++] = logs[i];
        }
    }

    function testTimelockScheduleBatchAndExecuteBatch() public {
        address[] memory targets = new address[](2);
        targets[0] = TIMELOCK;
        targets[1] = TIMELOCK;
        uint256[] memory values = new uint256[](2);
        bytes[] memory payloads = new bytes[](2);
        payloads[0] = abi.encodeWithSelector(bytes4(0x8a99d586), uint256(111));
        payloads[1] = abi.encodeWithSelector(bytes4(0x8a99d586), uint256(222));
        bytes memory scheduleCall = abi.encodeWithSelector(bytes4(0x8b07f62b), targets, values, payloads, bytes32(0));
        bytes memory mismatchCall = abi.encodeWithSelector(bytes4(0x8b07f62b), targets, new uint256[](1), payloads, bytes32(0));
        expectRevertSelector(OUTSIDER, TIMELOCK, scheduleCall, bytes4(0x30cd7471));
        expectRevertSelector(TIMELOCK_OWNER, TIMELOCK, mismatchCall, bytes4(0xff633a38));
        vm.recordLogs();
        (bool ok,) = callAs(TIMELOCK_OWNER, TIMELOCK, scheduleCall);
        require(ok, "scheduleBatch failed");
        Vm.Log memory scheduled = onlyLog(vm.getRecordedLogs(), TIMELOCK, BATCH_SCHEDULED_TOPIC);
        bytes32 opId = scheduled.topics[1];
        bytes32 opSlot = keccak256(abi.encode(opId, uint256(2)));
        uint256 ready = uint256(vm.load(TIMELOCK, opSlot));
        require(ready == block.timestamp + MIN_DELAY, "batch ready timestamp");
        bytes memory executeCall = abi.encodeWithSelector(bytes4(0xa6cc2c8c), targets, values, payloads, bytes32(0));
        expectRevertSelector(OUTSIDER, TIMELOCK, executeCall, bytes4(0x30cd7471));
        expectRevertSelector(TIMELOCK_OWNER, TIMELOCK, executeCall, bytes4(0xf800799b));
        vm.warp(ready + 1);
        vm.recordLogs();
        (ok,) = callAs(TIMELOCK_OWNER, TIMELOCK, executeCall);
        require(ok, "executeBatch failed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 3, "executeBatch log count");
        require(logs[0].topics[0] == MIN_DELAY_TOPIC && logs[1].topics[0] == MIN_DELAY_TOPIC, "child call order");
        require(uint256(vm.load(TIMELOCK, bytes32(uint256(1)))) == 222, "second child effect missing");
        Vm.Log memory done = onlyLog(singleOpLog(logs, BATCH_EXECUTED_TOPIC), TIMELOCK, BATCH_EXECUTED_TOPIC);
        require(done.topics[1] == opId, "batch executed event id");
        require(abi.decode(done.data, (uint256)) == 2, "batch executed count");
        require(uint256(vm.load(TIMELOCK, opSlot)) == 1, "batch operation not marked done");
    }

    function testTimelockCancel() public {
        bytes memory payload = abi.encodeWithSelector(bytes4(0x8a99d586), uint256(777));
        bytes memory scheduleCall = abi.encodeWithSelector(bytes4(0xb0e58bc9), TIMELOCK, uint256(0), payload, bytes32(0));
        vm.recordLogs();
        (bool ok,) = callAs(TIMELOCK_OWNER, TIMELOCK, scheduleCall);
        require(ok, "schedule failed");
        bytes32 opId = onlyLog(vm.getRecordedLogs(), TIMELOCK, OP_SCHEDULED_TOPIC).topics[1];
        bytes32 opSlot = keccak256(abi.encode(opId, uint256(2)));
        require(uint256(vm.load(TIMELOCK, opSlot)) != 0, "not scheduled");
        bytes memory cancelCall = abi.encodeWithSelector(bytes4(0xc4d252f5), opId);
        expectRevertSelector(OUTSIDER, TIMELOCK, cancelCall, bytes4(0x30cd7471));
        vm.recordLogs();
        (ok,) = callAs(TIMELOCK_OWNER, TIMELOCK, cancelCall);
        require(ok, "cancel failed");
        Vm.Log memory cancelled = onlyLog(vm.getRecordedLogs(), TIMELOCK, OP_CANCELLED_TOPIC);
        require(cancelled.topics[1] == opId, "cancelled event id");
        require(uint256(vm.load(TIMELOCK, opSlot)) == 0, "operation not cleared");
        expectRevertSelector(TIMELOCK_OWNER, TIMELOCK, cancelCall, bytes4(0x27c0d610));
    }
}