pragma solidity ^0.8.24;
interface Vm {
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
}
contract OldMultisigTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant FIRST = 0x73a83d746C38865960583879bC29bb007a04eacf;
    address constant SECOND = 0x324b0547039683C2df146421F3a76083EF130d27;
    address constant SIGNER1 = 0x7CE50A614174A3B26B107f1F9866f88461820626;
    address constant SIGNER2 = 0x8ceA98f6aB3004c762EFAf3dfd54876D62912300;
    address constant NEW1 = address(0x1111);
    address constant NEW2 = address(0x2222);
    address constant OUTSIDER = address(0x3333);
    function setUp() public {
        bytes memory runtime = vm.parseBytes(vm.readFile("runtime/Multisig.hex"));
        vm.etch(FIRST, runtime);
        vm.etch(SECOND, runtime);
        for (uint i; i < 2; ++i) {
            address target = i == 0 ? FIRST : SECOND;
            vm.store(target, bytes32(0), bytes32(uint256(uint160(SIGNER1))));
            vm.store(target, bytes32(uint256(1)), bytes32(uint256(uint160(SIGNER2))));
            vm.store(target, bytes32(uint256(2)), bytes32(i == 0 ? uint256(240) : uint256(1299)));
        }
    }
    function check(address target, uint256 count) internal {
        bytes memory update = abi.encodeWithSignature("updateSigners(address,address)", NEW1, NEW2);
        vm.prank(SIGNER1);
        (bool direct,) = target.call(update);
        require(!direct, "direct update succeeded");
        vm.prank(OUTSIDER);
        (bool outsider,) = target.call(abi.encodeWithSignature("submitTransaction(address,uint256,bytes,bool)", target, 0, update, true));
        require(!outsider, "outsider submit succeeded");
        vm.prank(SIGNER1);
        (bool success,) = target.call(abi.encodeWithSignature("submitTransaction(address,uint256,bytes,bool)", target, 0, update, true));
        require(success, "signer self update failed");
        require(vm.load(target, bytes32(0)) == bytes32(uint256(uint160(NEW1))), "new signer 1");
        require(vm.load(target, bytes32(uint256(1))) == bytes32(uint256(uint160(NEW2))), "new signer 2");
        require(uint256(vm.load(target, bytes32(uint256(2)))) == count + 1, "transaction count");
        vm.prank(SIGNER1);
        (bool oldSubmit,) = target.call(abi.encodeWithSignature("submitTransaction(address,uint256,bytes,bool)", target, 0, update, false));
        require(!oldSubmit, "old signer retained authority");
        vm.prank(NEW1);
        (bool newSubmit,) = target.call(abi.encodeWithSignature("submitTransaction(address,uint256,bytes,bool)", target, 0, abi.encodeWithSignature("transactionCount()"), false));
        require(newSubmit, "new signer lacks authority");
    }
    function testFirstOlderMultisigOneSignerSelfUpdate() public { check(FIRST, 240); }
    function testSecondOlderMultisigOneSignerSelfUpdate() public { check(SECOND, 1299); }
}
