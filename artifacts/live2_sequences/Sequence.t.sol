pragma solidity ^0.8.24;

interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function warp(uint256) external;
    function roll(uint256) external;
    function chainId(uint256) external;
    function mockCall(address, bytes calldata, bytes calldata) external;
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function sign(uint256, bytes32) external returns (uint8, bytes32, bytes32);
    function addr(uint256) external returns (address);
    function writeLine(string calldata, string calldata) external;
    function record() external;
    function accesses(address) external returns (bytes32[] memory reads, bytes32[] memory writes);
}

contract SequenceTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant BATCH = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant TOKENOMICS = address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9)));
    address constant PAPER = address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e)));
    address constant KEEPER = address(uint160(uint256(0x000924736b5ef2f50d3dbb82b4b9e85b4c5a4b9d56)));
    address constant RELAYER = address(uint160(uint256(0x002222222222222222222222222222222222222222)));
    address constant STAKING = address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016)));
    address constant STRANGER = address(uint160(uint256(0x001111111111111111111111111111111111111111)));
    address constant OWNER = address(uint160(uint256(0x00b915fa41e824d6aa31bb833ee81220c0f2c8ea0f)));
    bytes32 constant CLOSE_TYPEHASH = 0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13;
    bytes32 constant OPEN_TYPEHASH = 0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983;
    bytes32 constant WITHDRAW_TYPEHASH = 0xac4ddb8d63e9d7a862c5d61ce47517623a448262414a7eef6797102104b31214;
    bytes32 constant DOMAIN = 0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77;
    bytes32 constant CLOSED_TOPIC = 0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf;
    bytes32 constant LIQUIDATED_TOPIC = 0x0c859bc5db091ba3b9dc10c00f8dfc78b1f0b7e2566d107253ae67c069ae5de8;
    bytes32 constant ENQUEUED_TOPIC = 0xb2f6a0be3228032ab1a6e4d114ab0a4b8277ef32d9bd9b666e8537200aed4dc7;
    bytes32 constant CALL_EXECUTED_TOPIC = 0x8a23ef1120f3e42e722a0c0a599a66d55ab2650ecc39716f57e625684e349cad;
    uint256 constant INST = 1;
    uint256 constant WAD = 1e18;
    uint256 constant BIG = 4982012573755118958351370;
    uint256 constant PK = 0xb0b;
    uint256 constant USER_KEY = 0xa11ce;
    address constant STATUS = address(uint160(0x0810));
    // The signed open and close are session-key signed; the signed withdrawal is user signed,
    // so the user is a key this harness holds.
    address USER;

    struct Call { address target; bytes data; bool continueOnFailure; bytes32 intentId; bytes32 extra; }

    function setUp() public {
        vm.chainId(999);
        vm.roll(48901631);
        vm.warp(1792356638);
        USER = vm.addr(USER_KEY);
        // The BatchExecutor gates executeBatch on authorizedRelayers (mapping base 4): mirror the
        // pinned state's relayer authorization so the venue's own batch path can be driven.
        vm.store(BATCH, keccak256(abi.encode(RELAYER, uint256(4))), bytes32(uint256(1)));
        vm.etch(address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee))), vm.parseBytes(vm.readFile("runtime/0f3febfc94876b0c895f7acecdc8f5c863b549ee.hex")));
        vm.etch(address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e))), vm.parseBytes(vm.readFile("runtime/233ff29b239abc1d7748605da9b205c3e008626e.hex")));
        vm.store(address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e))), 0x0000000000000000000000000000000000000000000000000000000000000000, 0x000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a20001);
        vm.store(address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e))), 0x0000000000000000000000000000000000000000000000000000000000000001, 0x0000000000000000000000008326eb8896e358717f10502ec73ce8d28e37b108);
        vm.store(address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e))), 0x0000000000000000000000000000000000000000000000000000000000000002, 0x000000000000000000000000aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016);
        vm.store(address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e))), 0x1780f0602e50edc4043072de0413890463837fadd4e5e686e2cedddbfbb34ab2, 0x0000000000000000000000000000000000000000000000000000000000000001);
        vm.store(address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e))), 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc, 0x000000000000000000000000e0bc9cc7b067060aafccbaa3e250700c9cdd7262);
        vm.etch(address(uint160(uint256(0x003333333333333333333333333333333333333333))), vm.parseBytes(vm.readFile("runtime/3333333333333333333333333333333333333333.hex")));
        vm.etch(address(uint160(uint256(0x003997ffc8cbd281d4fc8d0548e505ae2fbbbd985a))), vm.parseBytes(vm.readFile("runtime/3997ffc8cbd281d4fc8d0548e505ae2fbbbd985a.hex")));
        vm.etch(address(uint160(uint256(0x00433bd418ec92818a960585f4d5fae563e735bb4a))), vm.parseBytes(vm.readFile("runtime/433bd418ec92818a960585f4d5fae563e735bb4a.hex")));
        vm.etch(address(uint160(uint256(0x00600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f))), vm.parseBytes(vm.readFile("runtime/600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f.hex")));
        vm.etch(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), vm.parseBytes(vm.readFile("runtime/6cd5661646289fb6e65ea5c032310fded797d0a2.hex")));
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000002, 0x000000000000000000000000a9b4c7b7ca5835652d81e25739c870d49f39cc2e);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000003, 0x000000000000000000000000000000000000000000000000000000e8d4a51000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000004, 0x0000000000000000000000000000000000000000000000000000000000000008);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000005, 0x00000000000000000000000000000000000000000000000000000002540be400);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000006, 0x00000000000000000000000075174549dbbd44497d31a47e2e2d7406408d63d9);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000008, 0x0000000000000000000000000000000000000000000000000000000000000002);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x000000000000000000000000000000000000000000000000000000000000000e, 0x00000000000000000000000000000000000000000035d96453ebd242f9b44800);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000016, 0x00000000000794fcff327cf4d045a35500000000002a08e22de4c293a9678c16);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000017, 0x00000000000000000000000000000000000000000000000000470de4df820000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000018, 0x00000000000000000000000000000000000000000000000000470de4df820000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x000000000000000000000000000000000000000000000000000000000000001a, 0x000000000000184c646a76a13aae0b2500000000000000011d4dcc3fe4d5f966);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x000000000000000000000000000000000000000000000000000000000000001d, 0x00000000000000000000008326eb8896e358717f10502ec73ce8d28e37b10800);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000058, 0x000000000000000000000000233ff29b239abc1d7748605da9b205c3e008626e);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x277c7e846040c767a772481f7a1d8c165ee789ea93fc2ecb317be57fc248690f, 0x00000000000c55c10000000078274a46400c83c91b7ad35dea11f01ec3894756);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x277c7e846040c767a772481f7a1d8c165ee789ea93fc2ecb317be57fc2486910, 0x00010001000000006ad53015000002450000000000000137b547a731c0180000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x31caf646d2c00fec149098d54a53a7ec09188c0fdb130a8c39097dc159edf315, 0x00000000000c571500000000764274793ee9fdae1a2567667df698fd5bd4eff6);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x31caf646d2c00fec149098d54a53a7ec09188c0fdb130a8c39097dc159edf316, 0x00010001000000006ad5310c00000064000000000000003635c9adc5dea00000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc, 0x0000000000000000000000000f3febfc94876b0c895f7acecdc8f5c863b549ee);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x47d01ba714f2f0257c22f54c5fa7d0e539453ffe7c50135242e7d86999bc2c09, 0x0000000000000000000000000000000000000000000000000000000000000001);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x6d5257204ebe7d88fd91ae87941cb2dd9d8062b64ae5a2bd2d28ec40b9fbf6df, 0x000003e8000000000000002c28d1751327a700000000032d26d12e980b600000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x6d5257204ebe7d88fd91ae87941cb2dd9d8062b64ae5a2bd2d28ec40b9fbf6e0, 0x00016345785d8a00000001b0f51147891600000000084595161401484a000000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x6d5257204ebe7d88fd91ae87941cb2dd9d8062b64ae5a2bd2d28ec40b9fbf6e1, 0x00000000000000000000000000000000000000000000152d02c7e14af6800000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x8647f183c3f812af92e286582c51585e065362159df0d31566fc3548a4a1dbe3, 0x0000000000000000000000000000000000000000000000000000000000000001);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x8bba10d259d59967bf3780316bdcebeec7d35329f54332595b0213d6a45ac2ea, 0x0000000000000000000000000000000000000000000000000000000000154119);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xa1e06f88c9dc57b004ec951b732e9ee50b8ad29e3de4bcd073ee6384c06196c2, 0x0000000000000000000000000000000000000000000000000000000000153e4e);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xabb60eadb0f5e1c44288cd33eb32d64a9d74038b051e4861ee122c4bfe9ddfc7, 0x0000000000000000000000000000000000000000000000000000000000000001);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xb34fd4e65556265b4d3db0d1bf5bf48d66ef27c2ee9fabbfef040005ddaaa332, 0x0000000000000000000000000000000000000000000000000000000000000001);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xb7634ec2165a7280a285aac3ec10cf370eca86d8aa9d3243c90b2151434091ad, 0x000000000000000a00000069bb03c8c4644af0dd000000861b1c43de2b04a5af);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xba1967d0db7c970dc4997adaace7ed9c9bd944df15313bb2b21dd53c320d5e67, 0x0000000000000000000000000000000000000000000000312d3804efe14fcbcc);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xcf81868fe6764a0e2d48c3509bbfc8be74eafea7bd0d05ae747c02046c19f6f9, 0x0000000000000000000000000000000000000000000000db7f750ebd8503750a);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xed96beefd7c954db0827835ee27568a8c03181960461ee41b0033487f562a76e, 0x000000000000000000000000000000000000000000000002148675cd615bbc6a);
        vm.etch(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), vm.parseBytes(vm.readFile("runtime/75174549dbbd44497d31a47e2e2d7406408d63d9.hex")));
        vm.store(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), 0x0000000000000000000000000000000000000000000000000000000000000001, 0x0000000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a2);
        vm.store(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), 0x0000000000000000000000000000000000000000000000000000000000000002, 0x000000000000000000000000e40f17915daa230324030003a197cdaef2261c0e);
        vm.store(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), 0x0000000000000000000000000000000000000000000000000000000000000003, 0x000000000000000000000000000000000000000000042337a51c4fd96083140a);
        vm.store(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), 0x0000000000000000000000000000000000000000000000000000000000000004, 0x000000000000000000000000000000000000000000c3e87a5c89dec3896e726e);
        vm.store(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), 0x0000000000000000000000000000000000000000000000000000000000000005, 0x00000000000000000000000000000000000000000001a784379d99db42000000);
        vm.store(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), 0x0000000000000000000000000000000000000000000000000000000000000007, 0x0000000000000000000000000000000000000000000000056bc75e2d63100000);
        vm.store(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), 0x0000000000000000000000000000000000000000000000000000000000000008, 0x0000000000000000000000000000000000000000006342fd08f00f6378000000);
        vm.store(address(uint160(uint256(0x0075174549dbbd44497d31a47e2e2d7406408d63d9))), 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc, 0x000000000000000000000000600d1b9653fd47fc1543d1cc87f33ba2d2fdf48f);
        vm.etch(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), vm.parseBytes(vm.readFile("runtime/8326eb8896e358717f10502ec73ce8d28e37b108.hex")));
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0x0000000000000000000000000000000000000000000000000000000000000003, 0x0000000000000000000000006cd5661646289fb6e65ea5c032310fded797d0a2);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0x3601e017c0a295fd1934063e084cc979cf77dc8851b152786a82ba4b6d1eeff8, 0x00000000000000000000000000000000000000000000000000000000e1e5f96c);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc, 0x0000000000000000000000008a5069fe303e8f81e91825436e956d595032e558);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0x39684b31c837607fce9511d4c0d00f0efab9b1e9e860fddbe75a219ad3ee9c55, 0x0000000000000000000000000000000000000ef7ffffffffffffffffffff7fff);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0x71331f9683a1ffe919518c96d3b081ffb472886e47864cb9664360da2db66db7, 0x000000000000000000000000000000000000000000000000000000006af202a4);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0x7cb88552ac18fde615f0582ee0599bc8a0319fffb9cf153193d8b42183e1eb6e, 0x383ef800c438006f0e3fff0600000000000000fdffffc1ff9e0cf6c033b030fc);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0x8d16f04ba8449b129cbee3496f0443a996a0a821223b8831416b88dee3d87d51, 0x000000000000000000000000000000000000000000000000000000006af7555a);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0x8f6044b8440f3666a961ee9a26b08b0a48508ca803bea180501aa3ad8e312f3c, 0x00000000000000000000000000000000000000000000000000000000ad7ee624);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0xb8391606159611bf4e1b0e61072daf179a4e32b26ba6e948e1c78ba272e4028b, 0x000000000000000000000000000000000000000000000000000f1ffffefffffd);
        vm.store(address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108))), 0xf1d52b4b0fb31b47f6e4c6eea73c49ad3a240f987aaa63d9d8ff042cea99dad8, 0x00000000000000000000000000000000000000000000000000000000364cd0fe);
        vm.etch(address(uint160(uint256(0x008a5069fe303e8f81e91825436e956d595032e558))), vm.parseBytes(vm.readFile("runtime/8a5069fe303e8f81e91825436e956d595032e558.hex")));
        vm.etch(address(uint160(uint256(0x00a9b4c7b7ca5835652d81e25739c870d49f39cc2e))), vm.parseBytes(vm.readFile("runtime/a9b4c7b7ca5835652d81e25739c870d49f39cc2e.hex")));
        vm.store(address(uint160(uint256(0x00a9b4c7b7ca5835652d81e25739c870d49f39cc2e))), 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc, 0x0000000000000000000000003997ffc8cbd281d4fc8d0548e505ae2fbbbd985a);
        vm.etch(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), vm.parseBytes(vm.readFile("runtime/aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016.hex")));
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x0000000000000000000000000000000000000000000000000000000000000003, 0x000000000000000000000000e40f17915daa230324030003a197cdaef2261c0e);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x0000000000000000000000000000000000000000000000000000000000000005, 0x00000000000000000000000000000000000000001ba40d764ee27614309175ab);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x0000000000000000000000000000000000000000000000000000000000000006, 0x0000000000000000000000000000000000000000000b25fbbec2168742ae9a44);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x000000000000000000000000000000000000000000000000000000000000000d, 0x0000000000000000000000000000000000000000000000000000000000000001);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x0000000000000000000000000000000000000000000000000000000000000010, 0x000000000000000000000001233ff29b239abc1d7748605da9b205c3e008626e);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x0f71faad8d51da763939a70fa48b85b1eeba250c97408e17a37de00eda935d31, 0x000000000000000000000000000000000000003ffffffffffffffffffffffffb);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x1548e5406303278624467a5eaecb0ba22f025ebe15141063aab333f57d69ad72, 0x00000000000000000000000000000000000000000000000000000000bac9b766);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x22902a1430f4e954a4feb16066c9a4ffafda8d39a383d098e0b0ca44df69ab62, 0x000000000000000000000000000000000000000000007a64c646b75ca78c0c9a);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc, 0x000000000000000000000000e6e3519455170913c5c3bfe541dd918a2d0cbb15);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x58ec5db0f2590dd1425243ba62689a43734b2d37dfcacf30e72c000877d2244d, 0x000000000000000000000000000000000000000000000001f8ef693af39a2598);
        vm.store(address(uint160(uint256(0x00aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016))), 0x7066b97e403bb7ba2915b324df52cda394191457a3d3103a9cccacdd44a0cbcd, 0x0000000000000000000000000000000000000000000001a63eaefafa4b3f381c);
        vm.etch(address(uint160(uint256(0x00cd617f984158a4f5d287ddee0e8eb0fed204916d))), vm.parseBytes(vm.readFile("runtime/cd617f984158a4f5d287ddee0e8eb0fed204916d.hex")));
        vm.etch(address(uint160(uint256(0x00e0bc9cc7b067060aafccbaa3e250700c9cdd7262))), vm.parseBytes(vm.readFile("runtime/e0bc9cc7b067060aafccbaa3e250700c9cdd7262.hex")));
        vm.etch(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), vm.parseBytes(vm.readFile("runtime/e40f17915daa230324030003a197cdaef2261c0e.hex")));
        vm.store(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), 0x0000000000000000000000000000000000000000000000000000000000000004, 0x00000000000000000000000075174549dbbd44497d31a47e2e2d7406408d63d9);
        vm.store(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), 0x0000000000000000000000000000000000000000000000000000000000000005, 0x000000000000000000000000aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016);
        vm.store(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), 0x0000000000000000000000000000000000000000000000000000000000000006, 0x00000000000000000000000000000000000000001bdb92d9bb4c9efec562ecb5);
        vm.store(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), 0x0000000000000000000000000000000000000000000000000000000000000009, 0x000000000000000000000000aad6c7b0cc3014fc80ffedae0ed7ce5967b0f016);
        vm.store(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), 0x1c02db7e43f0df87d0f575ff9d37c4987b926108a975515dd1064b16d94aa1e3, 0x00000000000000000000000000000000000000001ba40d764ee27614309175ab);
        vm.store(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc, 0x000000000000000000000000433bd418ec92818a960585f4d5fae563e735bb4a);
        vm.store(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), 0x94a799c0cff3b021cd966f913f7b335a8c3dd99daa08630ce279c93296842c0e, 0x00000000000000000000000000000000000000000000007aa622bf968af68235);
        vm.store(address(uint160(uint256(0x00e40f17915daa230324030003a197cdaef2261c0e))), 0xbc953192e0efa08e2c3f8664b5de14bdf96dbe6ccc67bfe44eadb4702963fa7a, 0x00000000000000000000000000000000000000000000003e80afa64154eb9ec9);
        vm.etch(address(uint160(uint256(0x00e6e3519455170913c5c3bfe541dd918a2d0cbb15))), vm.parseBytes(vm.readFile("runtime/e6e3519455170913c5c3bfe541dd918a2d0cbb15.hex")));
        vm.etch(address(uint160(uint256(0x00e991817199363046da0a28da6fbad0284e4aa492))), vm.parseBytes(vm.readFile("runtime/e991817199363046da0a28da6fbad0284e4aa492.hex")));
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0x0000000000000000000000000000000000000000000000000000000000000019, 0x00000000000000000000000000000000000000000000000000470de4df820000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xb39221ace053465ec3453ce2b36430bd138b997ecea25c1043da0c366812b828, 0x000003e8000000010000001a3c8ed044f4c780000000032d26d12e980b600000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xb39221ace053465ec3453ce2b36430bd138b997ecea25c1043da0c366812b829, 0x00016345785d8a00000001b5be54f0a02200000000084595161401484a000000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xb39221ace053465ec3453ce2b36430bd138b997ecea25c1043da0c366812b82a, 0x00000000000000000000000000000000000000000000152d02c7e14af6800000);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xbbbb3b1da0cb0951f34c5e9db4606f934b7367b5284f29163e9e6fe67e1e97d6, 0x00000000000000640000056fbc4c6080bf3b86ed0000061abc0de940559b7145);
        vm.store(address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2))), 0xbbbb3b1da0cb0951f34c5e9db4606f934b7367b5284f29163e9e6fe67e1e97d7, 0x00000000000005e84cb9e470cf1d0e4300000000000006913df4d03b70245d4a);
        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(1)), abi.encode(uint256(251080), uint256(251090)));
    }

    // ---------------- value-conservation invariant ----------------

    function components() internal view returns (uint256 t, uint256 bal, uint256 lock, uint256 q,
                                                 uint256 stf, uint256 dev, int256 lp, int256 side) {
        uint256 p22 = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        uint256 p26 = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        t = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        bal = uint128(p22);
        lock = p22 >> 128;
        q = uint256(vm.load(EXCHANGE, bytes32(uint256(18))));
        stf = uint128(p26);
        dev = p26 >> 128;
        lp = int256(uint256(vm.load(TOKENOMICS, bytes32(uint256(3)))));
        side = int256(uint256(vm.load(EXCHANGE, bytes32(uint256(27)))));
    }

    // The value-conservation invariant. The side bucket is NOT a claim: at block 48,173,889 the
    // real chain reads treasury - reserved = 400296219202209635129 = trackedLp + totalQueued
    // (377424392655154164362 + 22871826547055470767) while slot 27 holds 400296219202209635129,
    // so adding it would double count the bankroll. `side` is reported separately as an earmark
    // of the spendable LP bankroll.
    function residual() internal view returns (int256) {
        (uint256 t, uint256 bal, uint256 lock, uint256 q, uint256 stf, uint256 dev, int256 lp, int256 side) = components();
        side;
        return int256(t) - (int256(bal) + int256(lock) + int256(q) + int256(stf) + int256(dev) + lp);
    }

    function u2s(uint256 v) internal pure returns (string memory) {
        if (v == 0) return "0";
        uint256 t = v; uint256 d;
        while (t != 0) { d++; t /= 10; }
        bytes memory b = new bytes(d);
        while (v != 0) { d--; b[d] = bytes1(uint8(48 + v % 10)); v /= 10; }
        return string(b);
    }
    function i2s(int256 v) internal pure returns (string memory) {
        return v < 0 ? string.concat("-", u2s(uint256(-v))) : u2s(uint256(v));
    }
    function hx(uint8 v) internal pure returns (bytes1) { return v < 10 ? bytes1(uint8(48 + v)) : bytes1(uint8(87 + v)); }
    function hexs(bytes memory d) internal pure returns (string memory) {
        bytes memory o = new bytes(d.length * 2);
        for (uint256 i; i < d.length; i++) { o[i*2] = hx(uint8(d[i]) >> 4); o[i*2+1] = hx(uint8(d[i]) & 0xf); }
        return string(o);
    }
    function errOf(bytes memory res) internal pure returns (string memory) {
        if (res.length < 4) return "none";
        uint256 v;
        for (uint256 i; i < 4; i++) v = (v << 8) | uint8(res[i]);
        bytes memory b = new bytes(8);
        for (uint256 i; i < 8; i++) b[i] = hx(uint8((v >> (4 * (7 - i))) & 0xf));
        string memory sel = string.concat("0x", string(b));
        // Error(string) and Panic(uint256) carry a payload; keep it for the ledger
        if (res.length >= 68 && v == 0x08c379a0) return string.concat(sel, ":", hexs(res));
        return sel;
    }

    function note2(string memory a, uint256 b) internal pure returns (string memory) {
        return string.concat(a, "=", u2s(b));
    }
    function step(string memory seq, string memory name, bool ok, bytes memory res, string memory note) internal {
        (uint256 t, uint256 bal, uint256 lock, uint256 q, uint256 stf, uint256 dev, int256 lp, int256 side) = components();
        string memory line = string.concat(seq, ",", name, ",", ok ? "1" : "0", ",", errOf(res));
        line = string.concat(line, ",", u2s(t), ",", u2s(bal), ",", u2s(lock), ",", u2s(q));
        line = string.concat(line, ",", u2s(stf), ",", u2s(dev), ",", i2s(lp), ",", i2s(side));
        line = string.concat(line, ",", i2s(residual()), ",", note);
        vm.writeLine("out/steps.csv", line);
    }

    // ---------------- fixtures and readers ----------------

    function userBalance() internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
    }
    function nextPositionId() internal view returns (uint256) {
        return uint256(vm.load(EXCHANGE, bytes32(uint256(11))));
    }
    function paperSupply() internal view returns (uint256) {
        return uint256(vm.load(PAPER, bytes32(uint256(6))));
    }
    function posSlot(uint256 id) internal pure returns (bytes32) { return keccak256(abi.encode(id, uint256(10))); }
    function posWord0(uint256 id) internal view returns (uint256) { return uint256(vm.load(EXCHANGE, posSlot(id))); }
    function posWord1(uint256 id) internal view returns (uint256) { return uint256(vm.load(EXCHANGE, bytes32(uint256(posSlot(id)) + 1))); }
    function posMargin(uint256 id) internal view returns (uint256) { return uint128(posWord1(id)); }
    function posLeverage(uint256 id) internal view returns (uint256) { return (posWord1(id) >> 128) & 0xffffffff; }
    function posEntry(uint256 id) internal view returns (uint256) { return posWord0(id) >> 192; }
    function posInstrument(uint256 id) internal view returns (uint256) { return (posWord0(id) >> 160) & 0xffffffff; }
    function posActive(uint256 id) internal view returns (bool) { return (posWord1(id) >> 224) & 1 == 1; }

    // A credited deposit: exactly the Exchange-side book effect of a sweep or a direct
    // credit (exchange_storage_behavior.md: treasury +, totalBalances + by the same amount).
    function creditUser(uint256 amount) internal {
        bytes32 bs = keccak256(abi.encode(USER, uint256(9)));
        vm.store(EXCHANGE, bs, bytes32(uint256(vm.load(EXCHANGE, bs)) + amount));
        uint256 packed = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        vm.store(EXCHANGE, bytes32(uint256(22)), bytes32((packed & ~uint256(type(uint128).max)) | uint128((packed & type(uint128).max) + amount)));
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(uint256(vm.load(EXCHANGE, bytes32(uint256(14)))) + amount));
    }
    // Force lpBankrollAvailable to a chosen value. The LP's tracked equity and the treasury
    // move together, so the identity survives the fixture: treasury = target + reserved and
    // trackedLp = target - queued - side (the LP has deployed the rest of its capital).
    function forceAvail(uint256 target) internal {
        (uint256 t, uint256 bal, uint256 lock, uint256 q, uint256 stf, uint256 dev, int256 lp, int256 side) = components();
        t; lp;
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(target + bal + lock + stf + dev));
        side;
        unchecked {
            vm.store(TOKENOMICS, bytes32(uint256(3)), bytes32(uint256(int256(target) - int256(q))));
        }
    }
    function forceQueued(uint256 amount) internal { vm.store(EXCHANGE, bytes32(uint256(18)), bytes32(amount)); }
    // The negative control for the invariant checker: locked margin with no matching debit.
    function writeUnfundedPosition(uint256 id, uint256 margin, uint256 leverage, uint256 entry) internal {
        uint256 w0 = (entry << 192) | (INST << 160) | uint256(uint160(USER));
        uint256 w1 = margin | (leverage << 128) | (uint256(block.timestamp & type(uint64).max) << 160) |
                     (uint256(1) << 240) | (uint256(1) << 224);
        vm.store(EXCHANGE, posSlot(id), bytes32(w0));
        vm.store(EXCHANGE, bytes32(uint256(posSlot(id)) + 1), bytes32(w1));
        uint256 packed = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        vm.store(EXCHANGE, bytes32(uint256(22)), bytes32((((packed >> 128) + margin) << 128) | uint128(packed)));
    }
    // A labelled fixture step, so every fixture write is its own row and the rows around it are
    // pure venue action.
    function fixtureAvail(uint256 target, string memory seq, string memory name) internal {
        forceAvail(target);
        step(seq, name, true, "", string.concat("fixture_lpBankrollAvailable=", u2s(target)));
    }
    function hexw(bytes32 w) internal pure returns (string memory) {
        return string.concat("0x", hexs(abi.encodePacked(w)));
    }
    // The saved prestate is a transaction read-set: the queue pointers (slot 16 head, slot 17 next id)
    // are absent and read as zero, while the live chain reads head 4 at the pin. This fixture writes the
    // pinned pair so a sequence can run against pointer values the chain itself produced.
    function fixtureQueuePointers(uint256 head, uint256 nextId, string memory seq, string memory name) internal {
        vm.store(EXCHANGE, bytes32(uint256(16)), bytes32(head));
        vm.store(EXCHANGE, bytes32(uint256(17)), bytes32(nextId));
        step(seq, name, true, "", string.concat("fixture_queue_head=", u2s(head), ",next=", u2s(nextId)));
    }
    function queueState() internal view returns (string memory) {
        return string.concat("queued=", u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(18))))),
               ",userQueued=", u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(19)))))),
               ",head=", u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(16))))),
               ",next=", u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(17))))),
               ",userHead=", u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(20)))))),
               ",userTail=", u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(21)))))),
               ",bal=", u2s(userBalance()));
    }
    function bankroll() internal view returns (uint256) {
        (bool ok, bytes memory res) = EXCHANGE.staticcall(abi.encodeWithSelector(bytes4(0x0cdd5fc4)));
        require(ok && res.length == 32, "bankroll");
        return abi.decode(res, (uint256));
    }
    function mockBbo(uint256 asset, uint64 bid, uint64 ask) internal {
        vm.mockCall(address(uint160(uint256(0x080e))), abi.encode(uint32(asset)), abi.encode(uint256(bid), uint256(ask)));
    }
    // The withdrawal path reads the HyperCore spot balance at precompile 0x0801 and reverts
    // NoCoreBalance() when the read is empty; this mirrors the pinned read shape (three words).
    function mockSpot(uint256 a, uint256 b, uint256 c) internal {
        bytes memory code = abi.encodePacked(hex"7f", bytes32(a), hex"6000527f", bytes32(b), hex"6020527f", bytes32(c), hex"60405260", hex"60", hex"6000f3");
        vm.etch(address(uint160(0x0801)), code);
    }
    function mockStatus(uint256 value) internal {
        bytes memory code = abi.encodePacked(hex"7f", bytes32(value), hex"60005260206000f3");
        vm.etch(STATUS, code);
    }

    // ---------------- real venue actions ----------------

    function registerSession(uint256 pk) internal {
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(vm.addr(pk), outer)), bytes32(uint256(block.timestamp + 3600)));
    }
    function openSigned(uint256 instrument, bool isLong, uint256 size, uint32 leverage,
                        uint64 nonce, bool useDebt) internal returns (bool, bytes memory) {
        registerSession(PK);
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(OPEN_TYPEHASH, USER, uint32(instrument), isLong,
            uint128(size), leverage, useDebt, nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, digest);
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0xec6783f0), USER, uint32(instrument),
            isLong, uint128(size), leverage, useDebt, nonce, deadline, v, r, s));
    }
    // Open through the venue and report the position id the venue itself assigned.
    function openPosition(bool isLong, uint256 size, uint32 leverage, uint64 nonce, bool useDebt,
                          string memory seq, string memory name) internal returns (uint256 id) {
        (bool ok, bytes memory res) = openSigned(INST, isLong, size, leverage, nonce, useDebt);
        id = type(uint256).max;
        if (ok && nextPositionId() > 0) id = nextPositionId() - 1;
        uint256 sideAgg = uint256(vm.load(EXCHANGE, 0xbbbb3b1da0cb0951f34c5e9db4606f934b7367b5284f29163e9e6fe67e1e97d6)) & ((uint256(1) << 96) - 1);
        string memory note = string.concat("size=", u2s(size), ",lev=", u2s(leverage), ",longside=", u2s(sideAgg),
            ",id=", id == type(uint256).max ? "none" : u2s(id),
            ",locked=", id == type(uint256).max ? "0" : u2s(posMargin(id)),
            ",entry=", id == type(uint256).max ? "0" : u2s(posEntry(id)),
            ",bal=", u2s(userBalance()));
        step(seq, name, ok, res, note);
    }
    function closeSigned(uint256[] memory ids, uint64 nonce) internal returns (bool, bytes memory) {
        registerSession(PK);
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, digest);
        vm.prank(BATCH);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce, deadline, v, r, s));
    }
    function closeAndLog(uint256[] memory ids, uint64 nonce, string memory seq, string memory name) internal {
        uint256 supplyBefore = paperSupply();
        uint256 balBefore = userBalance();
        vm.recordLogs();
        (bool ok, bytes memory res) = closeSigned(ids, nonce);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        int256 adjusted;
        uint256 exitPrice;
        uint256 queued;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length == 0) continue;
            if (logs[i].topics[0] == CLOSED_TOPIC) {
                (uint256 e, , int256 a, , ) = abi.decode(logs[i].data, (uint256, int256, int256, uint256, uint256));
                exitPrice = e; adjusted = a;
            } else if (logs[i].topics[0] == ENQUEUED_TOPIC && logs[i].data.length == 32) {
                // Enqueued(address indexed user, uint256 indexed nodeId, uint256 amount)
                queued = abi.decode(logs[i].data, (uint256));
            }
        }
        string memory note = string.concat("exit=", u2s(exitPrice), ",adj=", i2s(adjusted),
            ",queued=", u2s(queued), ",baldelta=", i2s(int256(userBalance()) - int256(balBefore)),
            ",mint=", i2s(int256(paperSupply()) - int256(supplyBefore)), ",logs=", u2s(logs.length));
        step(seq, name, ok, res, note);
    }
    function liquidateAndLog(uint256[] memory ids, string memory seq, string memory name) internal {
        vm.recordLogs();
        vm.prank(KEEPER);
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x599dc539), ids));
        Vm.Log[] memory logs = vm.getRecordedLogs();
        int256 adjusted;
        uint256 exitPrice;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length > 0 && logs[i].topics[0] == LIQUIDATED_TOPIC && logs[i].data.length >= 96) {
                (uint256 e, , int256 a) = abi.decode(logs[i].data, (uint256, int256, int256));
                exitPrice = e; adjusted = a;
            }
        }
        string memory note = string.concat("exit=", u2s(exitPrice), ",adj=", i2s(adjusted),
            ",bal=", u2s(userBalance()), ",logs=", u2s(logs.length));
        step(seq, name, ok, res, note);
    }
    // pushStakerFees() 0x7b9f5264 is permissionless: it moves the staker fee accumulator and the
    // LP surplus above the configured cap to Staking's ordinary balance.
    // Negative control for the selector question: an unknown selector must give the runtime's own
    // unsupported-selector error.
    function unknownSelectorAndLog(string memory seq, string memory name) internal {
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xdeadbeef)));
        step(seq, name, ok, res, "probe_unknown_selector");
    }
    function pushStakerFeesAndLog(string memory seq, string memory name) internal {
        pushStakerFeesAs(seq, name, STRANGER);
    }
    function pushStakerFeesAs(string memory seq, string memory name, address caller) internal {
        (uint256 t, uint256 bal, uint256 lock, uint256 q, uint256 stf, uint256 dev, int256 lp, int256 side) = components();
        t; lock; dev; side;
        vm.prank(caller);
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0x7b9f5264)));
        (uint256 t2, uint256 bal2, uint256 lock2, uint256 q2, uint256 stf2, uint256 dev2, int256 lp2, int256 side2) = components();
        t2; lock2; q2; dev2; side2;
        string memory note = string.concat("caller=", caller == STRANGER ? "stranger" : (caller == KEEPER ? "keeper" : "owner"),
            ",staker_fee_delta=", i2s(int256(stf2) - int256(stf)),
            ",balances_delta=", i2s(int256(bal2) - int256(bal)), ",lp_delta=", i2s(lp2 - lp),
            ",staking_bal=", u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(STAKING, uint256(9)))))));
        step(seq, name, ok, res, note);
    }
    function harvestAndLog(uint256 n, string memory seq, string memory name) internal {
        vm.prank(USER);
        (bool ok, bytes memory res) = EXCHANGE.call(abi.encodeWithSelector(bytes4(0xddc63262), n));
        uint256 paid = (ok && res.length == 32) ? abi.decode(res, (uint256)) : 0;
        step(seq, name, ok, res, string.concat("paid=", u2s(paid), ",bal=", u2s(userBalance())));
    }
    // The signed withdrawal is verified against the user, not a session key.
    function withdrawSigned(uint256 amount, uint64 nonce) internal returns (bool, bytes memory) {
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(WITHDRAW_TYPEHASH, USER, amount, nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(USER_KEY, digest);
        return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x8d09f23f), USER, amount, nonce, deadline, v, r, s));
    }
    function withdrawAndLog(uint256 amount, uint64 nonce, string memory seq, string memory name) internal {
        uint256 before = userBalance();
        (bool ok, bytes memory res) = withdrawSigned(amount, nonce);
        step(seq, name, ok, res, string.concat("signed=", u2s(amount), ",debit=",
            i2s(int256(before) - int256(userBalance())), ",bal=", u2s(userBalance())));
    }
    // The real BatchExecutor path: the allowlist lives in the saved prestate (slots 0 to 2).
    function runBatch(bytes[] memory payloads) internal returns (bool ok, bytes memory res) {
        Call[] memory calls = new Call[](payloads.length);
        for (uint256 i; i < payloads.length; ++i) {
            calls[i] = Call(EXCHANGE, payloads[i], true, bytes32(0), bytes32(0));
        }
        vm.prank(RELAYER);
        (ok, res) = BATCH.call(abi.encodeWithSelector(bytes4(0x251fb27d), calls));
    }
    function closePayload(uint256[] memory ids, uint64 nonce) internal returns (bytes memory) {
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), nonce, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, digest);
        return abi.encodeWithSelector(bytes4(0x2792e706), USER, ids, nonce, deadline, v, r, s);
    }
    // A debt-funded open, recording every storage word the call writes.
    function openDebt(uint256 size, uint32 leverage, uint64 nonce, string memory seq, string memory name) internal returns (uint256 id) {
        vm.record();
        id = openPosition(true, size, leverage, nonce, true, seq, name);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        reads;
        string memory note = string.concat("recorded_writes=", u2s(writes.length));
        for (uint256 i; i < writes.length && i < 10; i++) {
            note = string.concat(note, ",w", u2s(i), "=", hexw(writes[i]));
        }
        step(seq, string.concat(name, "_writes"), true, "", note);
    }
    // A debt-funded close, recording every storage word the call writes.
    function closeDebt(uint256 id, uint64 nonce, string memory seq, string memory name) internal {
        registerSession(PK);
        vm.record();
        closeAndLog(one(id), nonce, seq, name);
        (bytes32[] memory reads, bytes32[] memory writes) = vm.accesses(EXCHANGE);
        reads;
        string memory note = string.concat("recorded_writes=", u2s(writes.length));
        for (uint256 i; i < writes.length && i < 8; i++) {
            note = string.concat(note, ",w", u2s(i), "=", hexw(writes[i]));
        }
        step(seq, string.concat(name, "_writes"), true, "", note);
    }
    function one(uint256 id) internal pure returns (uint256[] memory ids) { ids = new uint256[](1); ids[0] = id; }

// s0: the invariant holds on the loaded prestate, and the checker detects a break.
    function test_s0_control_and_negative() public {
        step("s0", "load", true, "", "residual_expected=0");
        writeUnfundedPosition(900001, 20000 * WAD, 500, 251085);
        step("s0", "unfunded_position_negative_control", true, "", "margin_expected_in_residual=20000000000000000000000");
    }

    // s1: open then close at the same quote, five times, from the venue's own opens.
    function test_s1_open_close_same_price_cycles() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        step("s1", "deposit_credit", true, "", note2("credit", 1000000 * WAD));
        for (uint256 cycle; cycle < 5; cycle++) {
            uint256 id = openPosition(true, 5000 * WAD, 100, uint64(1000 + cycle), false,
                                      "s1", cycle == 0 ? "open_0" : "open_n");
            if (id == type(uint256).max) continue;
            closeAndLog(one(id), uint64(2000 + cycle), "s1", cycle == 0 ? "close_same_price_0" : "close_same_price_n");
        }
        step("s1", "final_claim", true, "", string.concat("balance=", u2s(userBalance()), ",locked=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(22))) >> 128))));
    }

    // s2: a solvent win then a loss, from the venue's own opens (fee, LP debit and mint accounting).
    function test_s2_win_then_loss() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        forceAvail(BIG);
        creditUser(1000000 * WAD);
        uint256 win = openPosition(true, 5000 * WAD, 100, 1100, false, "s2", "open_win");
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(win), 1101, "s2", "close_win_solvent");
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        uint256 loss = openPosition(true, 5000 * WAD, 100, 1102, false, "s2", "open_loss");
        mockBbo(INST, uint64(251085 - 1005), uint64(251085 - 995));
        closeAndLog(one(loss), 1103, "s2", "close_loss");
        step("s2", "after", true, "", note2("paper_supply", paperSupply()));
    }

    // s3: open then liquidate at the maintenance boundary, LP bankroll funded.
    function test_s3_open_then_liquidate() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        forceAvail(BIG);
        creditUser(1000000 * WAD);
        uint256 id = openPosition(true, 5000 * WAD, 100, 1200, false, "s3", "open");
        mockBbo(INST, uint64(248000), uint64(248010));
        liquidateAndLog(one(id), "s3", "liquidate");
        harvestAndLog(10, "s3", "harvest_empty_queue");
    }

    // s4: a legitimate queued win puts a claim in the queue, then a liquidation runs while the
    // queue is live: the M-02 branch, with the side bucket watched.
    function test_s4_queue_live_liquidation() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        uint256 q = openPosition(true, 5000 * WAD, 100, 1300, false, "s4", "open_queued_win");
        uint256 l = openPosition(true, 5000 * WAD, 100, 1301, false, "s4", "open_to_liquidate");
        forceAvail(0);
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(q), 1302, "s4", "close_win_queued");
        step("s4", "queue_live", true, "", string.concat("queued=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(18))))), ",avail=", u2s(bankroll())));
        mockBbo(INST, uint64(248000), uint64(248010));
        liquidateAndLog(one(l), "s4", "liquidate_while_queue_live");
        forceAvail(BIG);
        harvestAndLog(10, "s4", "harvest");
        harvestAndLog(10, "s4", "harvest_again");
    }

    // s5: a deferred win, then a funded harvest, then a second harvest.
    function test_s5_queued_win_then_harvest() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        uint256 id = openPosition(true, 5000 * WAD, 100, 1400, false, "s5", "open");
        forceAvail(0);
        step("s5", "avail_zero", true, "", "lpBankrollAvailable=0");
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(id), 1401, "s5", "close_win_queued");
        forceAvail(BIG);
        step("s5", "avail_restored", true, "", "lpBankrollAvailable=big");
        harvestAndLog(10, "s5", "harvest_1");
        harvestAndLog(10, "s5", "harvest_2");
    }

    // s6: a legitimate loss while the queue is live, then a winner into the live queue.
    function test_s6_loss_into_live_queue_then_win() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        uint256 fill = openPosition(true, 5000 * WAD, 100, 1500, false, "s6", "open_fill_win");
        uint256 a = openPosition(true, 5000 * WAD, 100, 1501, false, "s6", "open_a");
        uint256 b = openPosition(true, 5000 * WAD, 100, 1502, false, "s6", "open_b");
        forceAvail(0);
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(fill), 1503, "s6", "close_fill_win_queued");
        mockBbo(INST, uint64(251085 - 1005), uint64(251085 - 995));
        closeAndLog(one(a), 1504, "s6", "close_a_loss_while_queued");
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(b), 1505, "s6", "close_b_win_into_live_queue");
        forceAvail(BIG);
        harvestAndLog(10, "s6", "harvest");
        harvestAndLog(10, "s6", "harvest_again");
    }

    // s7: both sides of one market in one block, closed in two orders.
    function test_s7_both_sides_one_market() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        uint256 lng = openPosition(true, 5000 * WAD, 100, 1600, false, "s7", "open_long");
        uint256 sht = openPosition(false, 5000 * WAD, 100, 1601, false, "s7", "open_short");
        uint256[] memory both = new uint256[](2);
        both[0] = lng; both[1] = sht;
        closeAndLog(both, 1602, "s7", "close_both_one_batch");
        uint256 lng2 = openPosition(true, 5000 * WAD, 100, 1603, false, "s7", "open_long_2");
        uint256 sht2 = openPosition(false, 5000 * WAD, 100, 1604, false, "s7", "open_short_2");
        mockBbo(INST, uint64(251085 + 495), uint64(251085 + 505));
        closeAndLog(one(lng2), 1605, "s7", "close_winner_first");
        mockBbo(INST, uint64(251085 - 505), uint64(251085 - 495));
        closeAndLog(one(sht2), 1606, "s7", "close_loser_second");
    }

    // s8: dust margin, the deadband boundary, the leverage bound and the per-side cap.
    function test_s8_boundaries() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        uint256 dust = openPosition(true, 1, 1, 1700, false, "s8", "open_one_wei");
        closeAndLog(one(dust), 1701, "s8", "close_one_wei_same_quote");
        mockBbo(INST, uint64(251085 + 5), uint64(251085 + 6));
        uint256 dead = openPosition(true, 5000 * WAD, 100, 1702, false, "s8", "open_deadband");
        closeAndLog(one(dead), 1703, "s8", "close_deadband_move");
        uint256 top = openPosition(true, 1000 * WAD, 1000, 1704, false, "s8", "open_leverage_bound");
        closeAndLog(one(top), 1705, "s8", "close_leverage_bound");
        openPosition(true, 1000 * WAD, 1001, 1706, false, "s8", "open_over_leverage");
        openPosition(true, 20000 * WAD, 100, 1707, false, "s8", "open_margin_20000");
        openPosition(true, 6000 * WAD, 100, 1708, false, "s8", "open_margin_6000");
        openPosition(false, 20000 * WAD, 100, 1709, false, "s8", "open_short_20000");
    }

    // s9: close then withdraw, with both HyperCore account-status replies.
    function test_s9_close_then_withdraw() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        mockSpot(10_000_000_000, 0, 0);
        step("s9", "spot_mock", true, "", "mock 0x0801 returns 10000000000,0,0");
        uint256 id = openPosition(true, 5000 * WAD, 100, 1800, false, "s9", "open");
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(id), 1801, "s9", "close_win");
        mockStatus(1);
        step("s9", "status_true", true, "", "mock 0x0810 returns 1");
        withdrawAndLog(2_000_000, 1802, "s9", "withdraw_status_true");
        vm.roll(block.number + 1);
        mockStatus(0);
        step("s9", "status_false", true, "", "mock 0x0810 returns 0, one withdrawal per user per block");
        withdrawAndLog(2_000_000, 1803, "s9", "withdraw_status_false");
    }

    // s10: two closes in one BatchExecutor transaction, through the real allowlist.
    function test_s10_batch_executor_two_closes() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        uint256 a = openPosition(true, 5000 * WAD, 100, 1900, false, "s10", "open_a");
        uint256 b = openPosition(false, 5000 * WAD, 100, 1901, false, "s10", "open_b");
        registerSession(PK);
        mockBbo(INST, uint64(251085 + 495), uint64(251085 + 505));
        bytes[] memory payloads = new bytes[](2);
        payloads[0] = closePayload(one(a), 1902);
        payloads[1] = closePayload(one(b), 1903);
        vm.recordLogs();
        (bool ok, bytes memory res) = runBatch(payloads);
        Vm.Log[] memory logs = vm.getRecordedLogs();
        uint256 executed;
        uint256 closed;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length == 0) continue;
            if (logs[i].topics[0] == CALL_EXECUTED_TOPIC && logs[i].emitter == BATCH) executed++;
            if (logs[i].topics[0] == CLOSED_TOPIC) closed++;
        }
        step("s10", "batch_two_closes", ok, res, string.concat("executed=", u2s(executed),
            ",closed_events=", u2s(closed), ",bal=", u2s(userBalance()), ",logs=", u2s(logs.length)));
    }

// s11: a debt-funded open against a coherent queue. The saved transaction read-set omits
// queue pointers, so seed the pinned head and next id before producing the deferred win.
    function test_s11_debt_cycle_coherent_queue() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        fixtureQueuePointers(4, 4, "s11", "fixture_queue_head4_next4");
        uint256 a = openPosition(true, 5000 * WAD, 100, 2400, false, "s11", "open_a");
        fixtureAvail(0, "s11", "fixture_avail_zero");
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(a), 2401, "s11", "close_a_win_queued");
        step("s11", "queue_state", true, "", queueState());
        uint256 debt = openDebt(1000 * WAD, 100, 2402, "s11", "open_debt_1000");
        step("s11", "after_open", true, "", queueState());
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeDebt(debt, 2403, "s11", "close_debt_same_quote");
        step("s11", "after_close", true, "", queueState());
        fixtureAvail(BIG, "s11", "fixture_avail_big");
        harvestAndLog(10, "s11", "harvest_once");
        step("s11", "after_harvest", true, "", queueState());
        openDebt(1000 * WAD, 100, 2404, "s11", "second_debt_open");
        step("s11", "end_state", true, "", queueState());
    }

    // s12: the LP surplus path with the LP cursor below its cap and negative.
    function test_s12_push_staker_fees_below_cap() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        forceAvail(0);
        step("s12", "lp_at_zero", true, "", "trackedLP=0");
        uint256 id = openPosition(true, 5000 * WAD, 100, 2100, false, "s12", "open");
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(id), 2101, "s12", "close_win_queued");
        step("s12", "lp_negative", true, "", string.concat("trackedLP=",
            i2s(int256(uint256(vm.load(TOKENOMICS, bytes32(uint256(3))))))));
        pushStakerFeesAndLog("s12", "push_stranger_lp_negative");
        pushStakerFeesAndLog("s12", "push_stranger_lp_negative_again");
    }

    // s13: the LP surplus path above the cap, twice, and with a live queue.
    function test_s13_push_staker_fees_above_cap() public {
        mockBbo(INST, uint64(251085 - 5), uint64(251085 + 5));
        creditUser(1000000 * WAD);
        forceAvail(5000000 * WAD + 1000 * WAD);
        step("s13", "lp_above_cap", true, "", "trackedLP=5001000e18");
        unknownSelectorAndLog("s13", "unknown_selector_control");
        pushStakerFeesAndLog("s13", "push_stranger_above_cap_1");
        pushStakerFeesAndLog("s13", "push_stranger_above_cap_2");
        pushStakerFeesAs("s13", "push_keeper_above_cap", KEEPER);
        pushStakerFeesAs("s13", "push_owner_above_cap", OWNER);
        uint256 a = openPosition(true, 5000 * WAD, 100, 2200, false, "s13", "open_a");
        uint256 b = openPosition(true, 5000 * WAD, 100, 2201, false, "s13", "open_b");
        forceAvail(5000000 * WAD + 1000 * WAD);
        mockBbo(INST, uint64(251085 + 995), uint64(251085 + 1005));
        closeAndLog(one(a), 2202, "s13", "close_win_queued");
        step("s13", "queue_live_with_excess", true, "", string.concat("queued=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(18))))), ",trackedLP=",
            i2s(int256(uint256(vm.load(TOKENOMICS, bytes32(uint256(3))))))));
        pushStakerFeesAndLog("s13", "push_with_live_queue");
        pushStakerFeesAndLog("s13", "push_with_live_queue_again");
        forceAvail(BIG);
        harvestAndLog(10, "s13", "harvest");
        if (b != type(uint256).max) closeAndLog(one(b), 2203, "s13", "close_b");
    }


}
