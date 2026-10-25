pragma solidity ^0.8.24;
interface Vm {
    struct Log { bytes32[] topics; bytes data; address emitter; }
    function etch(address, bytes calldata) external;
    function store(address, bytes32, bytes32) external;
    function load(address, bytes32) external view returns (bytes32);
    function prank(address) external;
    function recordLogs() external;
    function getRecordedLogs() external returns (Log[] memory);
    function readFile(string calldata) external returns (string memory);
    function parseBytes(string calldata) external pure returns (bytes memory);
    function computeCreate2Address(bytes32, bytes32, address) external pure returns (address);
    function addr(uint256) external pure returns (address);
    function sign(uint256, bytes32) external pure returns (uint8, bytes32, bytes32);
    function chainId(uint256) external;
}
contract MockWriter {
    uint256 public calls;
    event RawAction(bytes action);
    function sendRawAction(bytes calldata action) external {
        calls++;
        emit RawAction(action);
    }
}
contract ReentrantToken {
    address public proxy;
    uint256 public swept;
    uint256 public rescued;
    constructor(address p) { proxy = p; }
    function transfer(address, uint256) external returns (bool) {
        (bool a,) = proxy.call(abi.encodeWithSelector(bytes4(0x925b3aad), uint64(0), uint64(1), uint64(0)));
        (bool b,) = proxy.call(abi.encodeWithSelector(bytes4(0x0c506e96), address(this), uint256(1)));
        swept = a ? 1 : 0;
        rescued = b ? 1 : 0;
        return true;
    }
}
contract Live2ProxiesTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    address constant PROXY = address(uint160(uint256(0x00f1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce)));
    address constant USER = address(uint160(uint256(0x00fb94d3404c1d3d9d6f08f79e58041d5ea95accfa)));
    address constant EXCHANGE = address(uint160(uint256(0x006cd5661646289fb6e65ea5c032310fded797d0a2)));
    address constant FACTORY = address(uint160(uint256(0x001629b7d46bef6e13ff754174fc9f32dea309b38f)));
    address constant SESSION = address(uint160(uint256(0x008326eb8896e358717f10502ec73ce8d28e37b108)));
    address constant BATCH = address(uint160(uint256(0x00233ff29b239abc1d7748605da9b205c3e008626e)));
    address constant CORE = address(0x3333333333333333333333333333333333333333);
    address constant MOCK_TOKEN = address(0x4444444444444444444444444444444444444444);
    address constant CLONE = address(uint160(0xA11CE));
    address constant ATTACKER = address(uint160(0xBADBAD));
    address constant VICTIM = address(uint160(0xC0FFEE));
    address constant OTHER = address(uint160(0xD00D));
    address constant EXCHANGE_IMPL = address(uint160(uint256(0x000f3febfc94876b0c895f7acecdc8f5c863b549ee)));
    bytes32 constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
    bytes32 constant STUCK_TOPIC =
        keccak256("StuckTokenWithdrawn(address,address,uint256)");
    bytes32 constant ACTION_TOPIC = keccak256("RawAction(bytes)");
    bytes32 constant REGISTER_TOPIC =
        keccak256("SessionKeyRegistered(address,address,uint64)");
    bytes32 constant EIP712_TYPEHASH =
        keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)");
    bytes32 constant REGISTER_TYPEHASH = 0xd3d9a309f635415423ab81e7e3fb16d2117cc8e1edc90506adde9eaa3855edd2;
    uint256 constant DS_NEWEST = 0x53a2ab5a64b3239d36b108fb4cd035ebb40ed3f71dec28e37966622670147e77;
    uint256 constant DS_EARLIER_1 = 0x148ad6651bcc1981a17c339cb9726dee6b4617126472e8236bad447c73665254;
    uint256 constant DS_EARLIER_2 = 0xcbedfe73b0acbbcf567c94f68358f2ed291e8e67060d57d48253b5c5063505e8;
    address constant E1_EXCHANGE = address(uint160(uint256(0x001b534e482b92bb6daff452cd12f2e35219e13493)));
    address constant E2_EXCHANGE = address(uint160(uint256(0x002ede04561914c61a5f49212609541934fd7f5901)));
    bytes32 constant WD_STRUCT_HASH = 0xa9e6b2f904dc14b63294e2103d006c6781bd25e32cbfb5d823122c68aa1b62d0;
    bytes32 constant WD_DIGEST = 0xc74fa4dc110a1b252eb594218544d1d3aaf5838b011dc746b3500bdb20b86595;
    address constant WD_USER = address(uint160(uint256(0x00b2dadf36151fb51fad1b66a09d56749a3578e532)));
    uint8 constant WD_V = 27;
    bytes32 constant WD_R = 0x9dcb3249dbe8788d41737f0fe76383e046a7ebcc951879be1bcdb526b30ac8e0;
    bytes32 constant WD_S = 0x3c784e7f7bd6934b564b1918f48ede138b8005a6509e9bf525acb158bb7e494a;
    uint256 constant PK = 0xA11CE;
    address constant SESSION_KEY = address(uint160(0x5EED));
    uint64 constant EXPIRY = 4_000_000_000;
    uint64 constant DEADLINE = 4_000_000_000;

    function setUp() public {
        vm.chainId(999);
        vm.etch(PROXY, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
        vm.etch(CORE, vm.parseBytes(vm.readFile("runtime/CoreWriter.hex")));
        vm.etch(EXCHANGE, vm.parseBytes(vm.readFile("runtime/ExchangeProxy.hex")));
        vm.etch(EXCHANGE_IMPL, vm.parseBytes(vm.readFile("runtime/ExchangeImpl.hex")));
        vm.store(EXCHANGE, IMPL_SLOT, bytes32(uint256(uint160(EXCHANGE_IMPL))));
    }

    function patch(bytes memory data, uint256 offset, bytes memory value) internal pure returns (bytes memory) {
        for (uint256 i; i < value.length; ++i) { data[offset + i] = value[i]; }
        return data;
    }

    function sweep(uint64 token, uint64 spot, uint64 perp) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(bytes4(0x925b3aad), token, spot, perp);
    }

    function rescue(address token, uint256 amount) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(bytes4(0x0c506e96), token, amount);
    }

    function expectRevert(bytes memory data, address actor, address target) internal {
        vm.recordLogs();
        vm.prank(actor);
        (bool ok,) = target.call(data);
        require(!ok, "expected revert");
        require(vm.getRecordedLogs().length == 0, "revert emitted a log");
    }

    // ---- angle 1: template, guards, destination -------------------------------------
    function testImmutableGetters() public {
        (bool a, bytes memory u) = PROXY.call(hex"4f8632ba");
        (bool b, bytes memory e) = PROXY.call(hex"d2f7265a");
        require(a && b, "getter failed");
        require(abi.decode(u, (address)) == USER && abi.decode(e, (address)) == EXCHANGE, "immutables");
    }

    function testGuardMasksTheEmbeddedWordTo160Bits() public {
        bytes memory runtime = vm.parseBytes(vm.readFile("runtime/Proxy.hex"));
        // poison the twelve inert high bytes of both embedded words; the low 20 bytes stay intact
        bytes memory junk = hex"deadbeefdeadbeefdeadbeef";
        patch(runtime, 0x37b, junk);
        patch(runtime, 0x3da, junk);
        patch(runtime, 0x61, junk);
        patch(runtime, 0xde, junk);
        vm.etch(CLONE, runtime);
        vm.prank(USER);
        (bool ok,) = CLONE.call(rescue(MOCK_TOKEN, 1));
        require(ok, "rescue blocked by inert high bytes");
        vm.prank(EXCHANGE);
        (bool ok2,) = CLONE.call(sweep(7, 1, 0));
        require(ok2, "sweep blocked by inert high bytes");
        // control: changing the 20-byte address itself must break the guard
        bytes memory other = new bytes(20);
        for (uint256 i; i < 20; ++i) { other[i] = bytes20(OTHER)[i]; }
        bytes memory runtime2 = vm.parseBytes(vm.readFile("runtime/Proxy.hex"));
        patch(runtime2, 0x37b + 12, other);
        patch(runtime2, 0x3da + 12, other);
        vm.etch(CLONE, runtime2);
        expectRevert(rescue(MOCK_TOKEN, 1), USER, CLONE);
        vm.etch(CLONE, vm.parseBytes(vm.readFile("runtime/Proxy.hex")));
    }

    function testSweepDestinationIsTheEmbeddedWord() public {
        vm.recordLogs();
        vm.prank(EXCHANGE);
        (bool ok,) = PROXY.call(sweep(0xdead, 123, 0));
        require(ok, "sweep failed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].emitter == CORE, "one action");
        bytes memory raw = abi.decode(logs[0].data, (bytes));
        // action 6 payload: version||actionId, then abi.encode(destination, token, wei)
        require(raw.length == 100, "payload length");
        bytes memory params = new bytes(96);
        for (uint256 i; i < 96; ++i) { params[i] = raw[4 + i]; }
        (address destination, uint64 tokenId, uint64 amount) = abi.decode(params, (address, uint64, uint64));
        require(destination == EXCHANGE, "destination is the embedded exchange, not calldata");
        require(tokenId == 0xdead, "token echoed");
        require(amount == 123, "amount");
        // a caller-supplied address argument cannot move the destination
        vm.prank(EXCHANGE);
        (bool ok2,) = PROXY.call(sweep(uint64(uint160(ATTACKER)), 1, 0));
        require(ok2, "second sweep");
    }

    function testCopyOfTheCreationCodeIsPermissionless() public {
        bytes memory initcode = abi.encodePacked(vm.parseBytes(vm.readFile("runtime/Body.hex")),
                                                 abi.encode(ATTACKER, VICTIM));
        bytes32 salt = keccak256(abi.encodePacked(VICTIM));
        address clone;
        assembly { clone := create2(0, add(initcode, 0x20), mload(initcode), salt) }
        require(clone != address(0), "clone deploy failed");
        require(clone != PROXY, "clone address");
        (bool a, bytes memory u) = clone.call(hex"4f8632ba");
        (bool b, bytes memory e) = clone.call(hex"d2f7265a");
        require(a && b && abi.decode(u, (address)) == VICTIM && abi.decode(e, (address)) == ATTACKER,
                "clone words are the forged ones");
        // the clone is at the attacker's own CREATE2 address, not the factory's
        require(vm.computeCreate2Address(salt, keccak256(initcode),
                                         address(this)) == clone, "clone address formula");
        // the factory's own CREATE2 account for the same user uses the real exchange word and the
        // factory as the deployer, so it is a different address from the clone
        bytes memory factoryInitcode = abi.encodePacked(vm.parseBytes(vm.readFile("runtime/Prefix.hex")),
                                                        abi.encode(VICTIM));
        require(vm.computeCreate2Address(salt, keccak256(factoryInitcode), FACTORY) != clone
                && keccak256(factoryInitcode) != keccak256(initcode),
                "the factory's address for the victim is a different address");
        // the forged exchange word governs the clone's sweep, and the real Exchange cannot touch it
        vm.prank(ATTACKER);
        (bool s,) = clone.call(sweep(0, 1, 0));
        require(s, "forged exchange cannot sweep its own clone");
        expectRevert(sweep(0, 1, 0), EXCHANGE, clone);
        // the real factory proxy and the victim's real proxy are untouched
        (bool c, bytes memory e2) = PROXY.call(hex"d2f7265a");
        require(c && abi.decode(e2, (address)) == EXCHANGE, "real proxy untouched");
    }

    // ---- angle 2: factory binding ---------------------------------------------------
    function testCreate2TripleBindingControls() public {
        address[6] memory users = [address(uint160(uint256(0x00fb94d3404c1d3d9d6f08f79e58041d5ea95accfa))), address(uint160(uint256(0x00d75ffb585ff88d3aa50b7cf9230b27a7eb923c20))), address(uint160(uint256(0x002aa0b0bb38c2ab899797328e0796999d350d34c6))), address(uint160(uint256(0x0039c78ce4fbd59722f48a3271fe11f9ac5f933ba0))), address(uint160(uint256(0x000be4a0220b483b52f7cc607ea7b3f77d4953ae01))), address(uint160(uint256(0x00f163983b2f71a136a841355a650a1f9c974c46ab)))];
        address[6] memory proxies = [address(uint160(uint256(0x00f1c374b6a93ebdd1f1ff0ccd0ebbe8a7ab3840ce))), address(uint160(uint256(0x008a4712766b7884aca9b7d05ef7802afb3ec365ab))), address(uint160(uint256(0x0075582fd06f0cf63844fd9be7c409318807a8cf9a))), address(uint160(uint256(0x00b6ce2292dee6f7760116a19ff35b98846d824062))), address(uint160(uint256(0x003d674ec460c279cd000e672411c96b849f6e8802))), address(uint160(uint256(0x00713b6eb6e0efe1024278f0510fef2b92aa09011a)))];
        bytes memory prefix = vm.parseBytes(vm.readFile("runtime/Prefix.hex"));
        for (uint256 i; i < users.length; ++i) {
            bytes memory initcode = abi.encodePacked(prefix, abi.encode(users[i]));
            bytes32 salt = keccak256(abi.encodePacked(users[i]));
            require(vm.computeCreate2Address(salt, keccak256(initcode), FACTORY) == proxies[i],
                    "salt + code + user triple");
            // control 1: a different user word under the same salt
            bytes memory other = abi.encodePacked(prefix, abi.encode(VICTIM));
            require(vm.computeCreate2Address(salt, keccak256(other), FACTORY) != proxies[i], "code control");
            // control 2: a different salt under the same code
            bytes32 otherSalt = keccak256(abi.encodePacked(VICTIM));
            require(vm.computeCreate2Address(otherSalt, keccak256(initcode), FACTORY) != proxies[i], "salt control");
            // control 3: the same initcode from a different deployer is a different address
            require(vm.computeCreate2Address(salt, keccak256(initcode), ATTACKER) != proxies[i], "deployer control");
        }
    }

    // ---- angle 3: domains across suites ---------------------------------------------
    function dsFor(address verifying) internal pure returns (bytes32) {
        return keccak256(abi.encode(EIP712_TYPEHASH, keccak256(bytes("String")),
                                    keccak256(bytes("1")), uint256(999), verifying));
    }

    function testDomainFormulaAndCrossSuiteEcrecover() public {
        require(uint256(dsFor(EXCHANGE)) == DS_NEWEST, "newest domain");
        require(uint256(dsFor(E1_EXCHANGE)) == DS_EARLIER_1, "earlier_1 domain");
        require(uint256(dsFor(E2_EXCHANGE)) == DS_EARLIER_2, "earlier_2 domain");
        require(kesha(DS_NEWEST) == WD_DIGEST, "recorded digest formula");
        require(recover(DS_NEWEST) == WD_USER, "positive control: newest domain recovers the user");
        require(recover(DS_EARLIER_1) != WD_USER && recover(DS_EARLIER_1) != address(0),
                "earlier_1 replay does not recover the user");
        require(recover(DS_EARLIER_2) != WD_USER && recover(DS_EARLIER_2) != address(0),
                "earlier_2 replay does not recover the user");
        require(dsFor(EXCHANGE) != bytes32(DS_EARLIER_1) && dsFor(EXCHANGE) != bytes32(DS_EARLIER_2)
                && dsFor(E1_EXCHANGE) != dsFor(E2_EXCHANGE), "domains distinct");
    }

    function kesha(uint256 ds) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(hex"1901", bytes32(ds), WD_STRUCT_HASH));
    }

    function recover(uint256 ds) internal pure returns (address) {
        return ecrecover(kesha(ds), WD_V, WD_R, WD_S);
    }

    function registerCalldata(address user, address key, uint64 expiry, uint256 nonce,
                              uint8 v, bytes32 r, bytes32 s) internal pure returns (bytes memory) {
        return abi.encodeWithSelector(bytes4(0x5f76a1d6), user, key, expiry, address(0),
                                      nonce, DEADLINE, v, r, s);
    }

    function registrationDigest(address user, address key, uint64 expiry, uint256 nonce)
        internal pure returns (bytes32) {
        bytes32 structHash = keccak256(abi.encode(REGISTER_TYPEHASH, user, key, expiry,
                                                  address(0), nonce, uint64(DEADLINE)));
        return keccak256(abi.encodePacked(hex"1901", dsFor(EXCHANGE), structHash));
    }

    function testCrossSuiteRegistrationIsRejected() public {
        vm.etch(SESSION, vm.parseBytes(vm.readFile("runtime/Session.hex")));
        vm.store(SESSION, bytes32(uint256(3)), bytes32(uint256(uint160(EXCHANGE))));
        vm.store(SESSION, bytes32(uint256(1)), bytes32(uint256(DS_NEWEST)));
        vm.store(SESSION, keccak256(abi.encode(BATCH, uint256(7))), bytes32(uint256(1)));
        address user = vm.addr(PK);
        address key = SESSION_KEY;
        uint256 nonce = 0;

        // control: the newest suite's own domain parameters accept the signature
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, registrationDigest(user, key, EXPIRY, nonce));
        vm.recordLogs();
        vm.prank(BATCH);
        (bool ok,) = SESSION.call(registerCalldata(user, key, EXPIRY, nonce, v, r, s));
        require(ok, "registration under its own domain must succeed");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        bool emitted;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].topics.length > 0 && logs[i].topics[0] == REGISTER_TOPIC) { emitted = true; }
        }
        require(emitted, "SessionKeyRegistered");

        // cross-suite: the identical signature and struct, under each older suite's domain
        uint256[2] memory oldDomains = [uint256(DS_EARLIER_1), uint256(DS_EARLIER_2)];
        address[2] memory oldExchanges = [E1_EXCHANGE, E2_EXCHANGE];
        for (uint256 i; i < 2; ++i) {
            vm.store(SESSION, bytes32(uint256(1)), bytes32(oldDomains[i]));
            vm.store(SESSION, bytes32(uint256(3)), bytes32(uint256(uint160(oldExchanges[i]))));
            vm.prank(BATCH);
            (bool bad, bytes memory ret) = SESSION.call(
                registerCalldata(user, key, EXPIRY, nonce + 1 + i, v, r, s));
            require(!bad, "cross-suite registration must fail");
            require(bytes4(ret) == bytes4(0x8baa579f), "InvalidSignature()");
        }

        // control: the same older-domain parameters accept a signature made for them
        vm.store(SESSION, bytes32(uint256(1)), bytes32(DS_EARLIER_2));
        vm.store(SESSION, bytes32(uint256(3)), bytes32(uint256(uint160(E2_EXCHANGE))));
        bytes32 structHash = keccak256(abi.encode(REGISTER_TYPEHASH, user, key, EXPIRY,
                                                  address(0), uint256(5), uint64(DEADLINE)));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", dsFor(E2_EXCHANGE), structHash));
        (uint8 v2, bytes32 r2, bytes32 s2) = vm.sign(PK, digest);
        vm.prank(BATCH);
        (bool ok2,) = SESSION.call(registerCalldata(user, key, EXPIRY, 5, v2, r2, s2));
        require(ok2, "older-domain control must succeed on the same runtime");
    }

    function testRegistrationBindsTheSignedExpiry() public {
        vm.etch(SESSION, vm.parseBytes(vm.readFile("runtime/Session.hex")));
        vm.store(SESSION, bytes32(uint256(3)), bytes32(uint256(uint160(EXCHANGE))));
        vm.store(SESSION, bytes32(uint256(1)), bytes32(uint256(DS_NEWEST)));
        vm.store(SESSION, keccak256(abi.encode(BATCH, uint256(7))), bytes32(uint256(1)));
        address user = vm.addr(PK);
        address key = SESSION_KEY;
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(PK, registrationDigest(user, key, EXPIRY, 7));
        // the user signed a different expiry; the raw signature must not register the longer one
        vm.prank(BATCH);
        (bool ok, bytes memory ret) = SESSION.call(
            registerCalldata(user, key, EXPIRY + 86_400, 7, v, r, s));
        require(!ok, "extended expiry must not register");
        require(bytes4(ret) == bytes4(0x8baa579f), "InvalidSignature()");
        // control: the signed expiry itself registers
        vm.prank(BATCH);
        (bool ok2,) = SESSION.call(registerCalldata(user, key, EXPIRY, 7, v, r, s));
        require(ok2, "the signed expiry registers");
    }

    // ---- angle 4: rescue aimability -------------------------------------------------
    function testRescueAtACoreFacingTargetReverts() public {
        // the captured CoreWriter dispatches only sendRawAction(bytes); a transfer-shaped call is rejected
        vm.recordLogs();
        (bool direct,) = CORE.call(abi.encodeWithSelector(bytes4(0x17938e13), hex"01000007"));
        require(direct, "the captured CoreWriter accepts its own selector");
        expectRevert(rescue(CORE, 1), USER, PROXY);
        // positive control: an ordinary ERC-20 that returns true is rescued
        vm.etch(MOCK_TOKEN, hex"600160005260206000f3");
        vm.recordLogs();
        vm.prank(USER);
        (bool ok,) = PROXY.call(rescue(MOCK_TOKEN, 11));
        require(ok, "rescue of a normal token succeeds");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        require(logs.length == 1 && logs[0].topics[0] == STUCK_TOPIC, "rescue event");
    }

    function testRescueAtBookkeepingOrTheExchangeReverts() public {
        expectRevert(rescue(PROXY, 1), USER, PROXY);
        expectRevert(rescue(CORE, type(uint256).max), USER, PROXY);
        // the pinned Exchange proxy and implementation are etched, so its delegation is live here
        (bool delegated,) = EXCHANGE.staticcall(hex"13dd495b");
        require(delegated, "the Exchange proxy delegates to its implementation");
        expectRevert(rescue(EXCHANGE, 1), USER, PROXY);
        // the proxy keeps no storage: a seeded word is untouched by a sweep and a rescue
        vm.store(PROXY, bytes32(uint256(0)), bytes32(uint256(0x1234)));
        vm.store(PROXY, bytes32(uint256(7)), bytes32(uint256(0x5678)));
        vm.etch(MOCK_TOKEN, hex"600160005260206000f3");
        vm.prank(USER);
        PROXY.call(rescue(MOCK_TOKEN, 1));
        vm.prank(EXCHANGE);
        PROXY.call(sweep(7, 1, 0));
        require(uint256(vm.load(PROXY, bytes32(uint256(0)))) == 0x1234
             && uint256(vm.load(PROXY, bytes32(uint256(7)))) == 0x5678, "proxy storage untouched");
    }

    function testTokenReentrancyCannotReachEitherGuard() public {
        ReentrantToken token = new ReentrantToken(PROXY);
        vm.recordLogs();
        vm.prank(USER);
        (bool ok,) = PROXY.call(rescue(address(token), 1));
        require(ok, "outer rescue succeeds");
        require(token.swept() == 0 && token.rescued() == 0,
                "both re-entrant calls were rejected by the caller guards");
        Vm.Log[] memory logs = vm.getRecordedLogs();
        for (uint256 i; i < logs.length; ++i) {
            require(logs[i].topics[0] != ACTION_TOPIC, "no Core action from the re-entrant attempt");
        }
    }
}
