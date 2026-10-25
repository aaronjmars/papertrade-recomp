pragma solidity ^0.8.24;
interface Vm {
 struct Log { bytes32[] topics; bytes data; address emitter; }
 function recordLogs() external;
 function getRecordedLogs() external returns (Log[] memory);
 function etch(address, bytes calldata) external;
 function store(address, bytes32, bytes32) external;
 function load(address, bytes32) external view returns (bytes32);
 function prank(address) external;
 function sign(uint256, bytes32) external returns (uint8,bytes32,bytes32);
 function addr(uint256) external returns (address);
 function roll(uint256) external;
 function warp(uint256) external;
}
contract CoreBboLower { fallback() external { assembly { mstore(0,271610) mstore(32,271620) return(0,64) } } }
contract CoreBboUpper { fallback() external { assembly { mstore(0,271810) mstore(32,271820) return(0,64) } } }
contract CoreStatusMock { fallback() external { assembly { mstore(0,1) return(0,32) } } }
contract CoreSpotMock { fallback() external { assembly { mstore(0,6509967368792354) mstore(32,0) mstore(64,0) return(0,96) } } }
contract CoreWriterMock { event WriterCall(bytes data); fallback() external payable { emit WriterCall(msg.data); } }
contract DebtOpenTest {
 Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
 address constant EXCHANGE = address(uint160(uint256(0x001b534e482b92bb6daff452cd12f2e35219e13493)));
 address constant SESSION = address(uint160(uint256(0x0091667db7e20474b3ac6eaabf0c8106ed46b5691a)));
 address constant BATCH = address(uint160(uint256(0x004041882573028cb177847c46f82e242024ebde66)));
 address constant USER = address(uint160(uint256(0x000000000000000000000000057d2403654b2ba82d4d95d0e0ffa2550e8140f4)));
 address constant BBO = address(0x080e);
 bytes32 constant DOMAIN = 0x148ad6651bcc1981a17c339cb9726dee6b4617126472e8236bad447c73665254;
 bytes32 constant TYPEHASH = 0xfce2fb41f9ff0457a0f012e62cfd6a7cff4e8439ae20008ab6979c740ba5a983;
 bytes32 constant CLOSE_TYPEHASH = 0x9cc23a52214afa42e1ae53cdb2e79dc2d0cd33c33faca383ed3b149300adcb13;
 uint256 constant MARGIN = 25e18;
 uint256 constant NONCE = 1000000;
 uint256 constant PK = 0xb0b;
 uint256 constant POSITION_ID = 398939;
 function mapSlot(uint256 key,uint256 base) internal pure returns (bytes32) { return keccak256(abi.encode(key,base)); }
 function userSlot(uint256 base) internal pure returns (bytes32) { return mapSlot(uint256(uint160(USER)),base); }
 function nodeSlot(uint256 id) internal pure returns (bytes32) { return mapSlot(id,15); }
 function positionWord(uint256 id) internal view returns (uint256) { return uint256(vm.load(EXCHANGE,bytes32(uint256(mapSlot(id,10))+1))); }
 function setupSigner() internal {
  address key=vm.addr(PK);
  bytes32 outer=userSlot(4);
  bytes32 slot=keccak256(abi.encode(key,outer));
  vm.store(SESSION,slot,bytes32(uint256(block.timestamp+3600)));
 }
 function setUp() public {
  vm.etch(BBO,hex"7f000000000000000000000000000000000000000000000000000000000004255e6000527f000000000000000000000000000000000000000000000000000000000004256860205260406000f3");
  require(block.chainid==999 && block.number==47721328,"fork identity");
  require(EXCHANGE.codehash==0x93076ef48e1d48172af505f739606cf1fa8425dbf9dbc6bee6743307bd4bd63b,"Exchange proxy runtime");
  require(address(0x557c853E100600e0Ee91e0dF88fCF4aF0097fF89).codehash==0x4fb669a254fa857e1c52da492625e2f4aa4f970f9f3ff8f80db8ecf41ac175bd,"Exchange implementation runtime");
  require(SESSION.codehash==0x93076ef48e1d48172af505f739606cf1fa8425dbf9dbc6bee6743307bd4bd63b,"Session proxy runtime");
  require(address(0xac8Ba1307815f74bd13d4D039c96f7B97e81AA49).codehash==0x23d9559d8bcf93e21027b102fbee55eba98f291ed237d2d24c62001e43b9b63a,"old library runtime");
  require(address(0x56bFedb00F1BA3Ecd4bD3fc1d5C597B6977328D3).codehash==0x337787e630c4fe48e2cea45e1dbd7cb12be2254d158042ee1cd446e706d5c484,"Session implementation runtime");
  require(uint256(vm.load(SESSION,bytes32(uint256(1))))==uint256(DOMAIN),"domain");
  (bool openHashOk,bytes memory openHashOut)=SESSION.staticcall(hex"6525a680");
  require(openHashOk && abi.decode(openHashOut,(bytes32))==TYPEHASH,"open typehash");
  (bool closeHashOk,bytes memory closeHashOut)=SESSION.staticcall(hex"208e24fc");
  require(closeHashOk && abi.decode(closeHashOut,(bytes32))==CLOSE_TYPEHASH,"close typehash");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(11))))==POSITION_ID,"next position id");
  setupSigner();
 }
 function seedQueue(uint256 amount) internal {
  uint256 node=uint256(vm.load(EXCHANGE,bytes32(uint256(17))));
  require(node==8453 && uint256(vm.load(EXCHANGE,bytes32(uint256(16))))==node,"queue base");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(18))))==0,"queue total base");
  vm.store(EXCHANGE,bytes32(uint256(17)),bytes32(node+1));
  vm.store(EXCHANGE,bytes32(uint256(18)),bytes32(amount));
  vm.store(EXCHANGE,userSlot(19),bytes32(amount));
  vm.store(EXCHANGE,userSlot(20),bytes32(node));
  vm.store(EXCHANGE,userSlot(21),bytes32(node));
  vm.store(EXCHANGE,nodeSlot(node),bytes32(uint256(uint160(USER))));
  vm.store(EXCHANGE,bytes32(uint256(nodeSlot(node))+1),bytes32(amount));
 }
 function signOpen(bool useDebt,uint256 nonce) internal returns (uint8 v,bytes32 r,bytes32 s) {
  uint64 deadline=uint64(block.timestamp+3600);
  bytes32 sh=keccak256(abi.encode(TYPEHASH,USER,uint32(1),false,uint128(MARGIN),uint32(75),useDebt,nonce,deadline));
  bytes32 digest=keccak256(abi.encodePacked(hex"1901",DOMAIN,sh));
  (v,r,s)=vm.sign(PK,digest);
  require(ecrecover(digest,v,r,s)==vm.addr(PK),"signer");
 }
 function openWithSig(bool useDebt,uint256 nonce,uint8 v,bytes32 r,bytes32 s) internal returns (bool,bytes memory) {
  vm.prank(BATCH);
  return EXCHANGE.call(abi.encodeWithSelector(bytes4(0xec6783f0),USER,uint32(1),false,uint128(MARGIN),uint32(75),useDebt,nonce,uint64(block.timestamp+3600),v,r,s));
 }
 function open(bool useDebt,uint256 nonce) internal returns (bool,bytes memory) {
  (uint8 v,bytes32 r,bytes32 s)=signOpen(useDebt,nonce);
  return openWithSig(useDebt,nonce,v,r,s);
 }
 function closeOne(uint256 id,uint256 nonce) internal returns (bool,bytes memory) {
  uint256[] memory ids=new uint256[](1);ids[0]=id;
  uint64 deadline=uint64(block.timestamp+3600);
  bytes32 idsHash=keccak256(abi.encodePacked(ids));
  bytes32 sh=keccak256(abi.encode(CLOSE_TYPEHASH,USER,idsHash,nonce,deadline));
  bytes32 digest=keccak256(abi.encodePacked(hex"1901",DOMAIN,sh));
  (uint8 v,bytes32 r,bytes32 sigs)=vm.sign(PK,digest);
  require(ecrecover(digest,v,r,sigs)==vm.addr(PK),"close signer");
  vm.prank(BATCH);
  return EXCHANGE.call(abi.encodeWithSelector(bytes4(0x2792e706),USER,ids,nonce,deadline,v,r,sigs));
 }
 function errorIs(bytes memory output,bytes4 selector) internal pure returns (bool) { return output.length==4 && bytes4(output)==selector; }
 function testOpenThenCloseDebtQueuesPayout() public {
  seedQueue(MARGIN);
  (bool opened,bytes memory openOut)=open(true,NONCE);
  require(opened && abi.decode(openOut,(uint256))==POSITION_ID,"debt open");
  require(uint256(vm.load(EXCHANGE,userSlot(19)))==0,"queue spent by open");
  (bool closed,bytes memory closeOut)=closeOne(POSITION_ID,NONCE+1);
  require(closed && closeOut.length==0,"debt close");
  require((positionWord(POSITION_ID)>>240)&0xff==0,"closed active flag");
  require(uint256(vm.load(EXCHANGE,userSlot(19)))>0,"queued payout");
  uint256 balanceBefore=uint256(vm.load(EXCHANGE,userSlot(9)));
  (bool harvested,bytes memory harvestOut)=EXCHANGE.call(abi.encodeWithSelector(bytes4(0xddc63262),uint256(1)));
  require(harvested,"harvest call");
  require(abi.decode(harvestOut,(uint256))==MARGIN,"harvest amount");
  require(uint256(vm.load(EXCHANGE,userSlot(19)))==0,"queue after harvest");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(18))))==0,"global queue after harvest");
  require(uint256(vm.load(EXCHANGE,userSlot(9)))==balanceBefore+MARGIN,"harvest balance credit");
 }
 function testDebtOpenCloseHarvestWithdrawToCore() public {
  seedQueue(MARGIN);
  vm.store(EXCHANGE,userSlot(9),bytes32(uint256(0)));
  (bool opened,bytes memory openOut)=open(true,NONCE);
  require(opened && abi.decode(openOut,(uint256))==POSITION_ID,"open");
  (bool closed,)=closeOne(POSITION_ID,NONCE+1);
  require(closed,"close");
  require(uint256(vm.load(EXCHANGE,userSlot(19)))==MARGIN,"close queue");
  (bool harvested,bytes memory harvestOut)=EXCHANGE.call(abi.encodeWithSelector(bytes4(0xddc63262),uint256(1)));
  require(harvested && abi.decode(harvestOut,(uint256))==MARGIN,"harvest");
  require(uint256(vm.load(EXCHANGE,userSlot(9)))==MARGIN,"harvest credit");
  vm.etch(address(0x0810),address(new CoreStatusMock()).code);
  vm.etch(address(0x0801),address(new CoreSpotMock()).code);
  vm.etch(address(0x3333333333333333333333333333333333333333),address(new CoreWriterMock()).code);
  vm.recordLogs();
  vm.prank(USER);
  (bool withdrawn,bytes memory withdrawalOut)=EXCHANGE.call(abi.encodeWithSelector(bytes4(0x7f99545a),uint256(25000000)));
  Vm.Log[] memory logs=vm.getRecordedLogs();
  require(withdrawn && withdrawalOut.length==0,"withdraw");
  require(uint256(vm.load(EXCHANGE,userSlot(9)))==0,"withdraw balance");
  require(uint256(vm.load(EXCHANGE,userSlot(19)))==0,"withdraw queue");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(18))))==0,"withdraw global queue");
  require(logs.length==2,"withdraw logs");
  bytes memory action=abi.encodePacked(bytes4(0x01000006),bytes32(uint256(uint160(USER))),bytes32(0),bytes32(uint256(2500000000)));
  bytes memory expectedWriterCall=abi.encodeWithSelector(bytes4(0x17938e13),action);
  require(logs[0].emitter==address(0x3333333333333333333333333333333333333333),"writer emitter");
  require(logs[0].topics.length==1 && logs[0].topics[0]==keccak256("WriterCall(bytes)"),"writer topic");
  require(keccak256(abi.decode(logs[0].data,(bytes)))==keccak256(expectedWriterCall),"writer calldata");
  require(logs[1].emitter==EXCHANGE,"withdraw event emitter");
  require(logs[1].topics.length==2 && logs[1].topics[0]==0x95d1a93901f24eeaa294588802f66fa008f9f3741060c9f79e5dab4709de5e75,"withdraw topic");
  require(logs[1].topics[1]==bytes32(uint256(uint160(USER))),"withdraw event user");
  (uint256 debited,uint256 coreAmount)=abi.decode(logs[1].data,(uint256,uint256));
  require(debited==MARGIN && coreAmount==2500000000,"withdraw event amount");
 }
 function testDebtCloseLowerPriceQueuesProfit() public {
  seedQueue(MARGIN);
  (bool opened,)=open(true,NONCE);require(opened,"profit open");
  vm.etch(BBO,address(new CoreBboLower()).code);
  (bool closed,)=closeOne(POSITION_ID,NONCE+1);require(closed,"profit close");
  uint256 amount=uint256(vm.load(EXCHANGE,userSlot(19)));
  require(amount==25331156061910525405,"profit queue amount");
 }
 function testDebtCloseHigherPriceQueuesLoss() public {
  seedQueue(MARGIN);
  (bool opened,)=open(true,NONCE);require(opened,"loss open");
  vm.etch(BBO,address(new CoreBboUpper()).code);
  (bool closed,)=closeOne(POSITION_ID,NONCE+1);require(closed,"loss close");
  uint256 amount=uint256(vm.load(EXCHANGE,userSlot(19)));
  require(amount==24309938722558563201,"loss queue amount");
 }
 function testNoQueueCreditReverts() public {
  (bool ok,bytes memory out)=open(true,NONCE);
  require(!ok && errorIs(out,0x8e667356),"no credit error");
 }
 function testBelowCreditReverts() public {
  vm.store(EXCHANGE,userSlot(19),bytes32(MARGIN-1));
  (bool ok,bytes memory out)=open(true,NONCE);
  require(!ok && errorIs(out,0x8e667356),"below credit error");
 }
 function testSignatureMutationRejected() public {
  (uint8 v,bytes32 r,bytes32 s)=signOpen(false,NONCE);
  (bool ok,bytes memory out)=openWithSig(true,NONCE,v,r,s);
  require(!ok && errorIs(out,0xc5045f22),"useDebt signed");
 }
 function testNonDebtOpenDebitsBalance() public {
  uint256 balance=uint256(vm.load(EXCHANGE,userSlot(9)));
  (bool ok,bytes memory out)=open(false,NONCE);
  require(ok,"nondebt open");
  uint256 id=abi.decode(out,(uint256));require(id==POSITION_ID,"id");
  require((positionWord(id)>>232)&0xff==0,"nondebt flag");
  require(uint256(vm.load(EXCHANGE,userSlot(9)))==balance-MARGIN,"balance debit");
 }
 function testExactCreditSetsFlagAndConsumesQueue() public {
  seedQueue(MARGIN);
  uint256 balance=uint256(vm.load(EXCHANGE,userSlot(9)));
  (bool ok,bytes memory out)=open(true,NONCE);
  require(ok,"debt open");
  uint256 id=abi.decode(out,(uint256));require(id==POSITION_ID,"id");
  require((positionWord(id)>>232)&0xff==1,"debt flag");
  require(uint256(vm.load(EXCHANGE,userSlot(9)))==balance,"balance unchanged");
  require(uint256(vm.load(EXCHANGE,userSlot(19)))==0,"user queue consumed");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(18))))==0,"global queue consumed");
  require(uint256(vm.load(EXCHANGE,userSlot(20)))==0,"user head cleared");
  require(uint256(vm.load(EXCHANGE,userSlot(21)))==0,"user tail cleared");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(nodeSlot(8453))+1)))==0,"node amount cleared");
 }
 function testPartialQueueCreditLeavesRemainder() public {
  seedQueue(MARGIN+5e18);
  (bool ok,bytes memory out)=open(true,NONCE);
  require(ok,"partial debt open");
  uint256 id=abi.decode(out,(uint256));require(id==POSITION_ID,"partial id");
  require((positionWord(id)>>232)&0xff==1,"partial debt flag");
  require(uint256(vm.load(EXCHANGE,userSlot(19)))==5e18,"partial user remainder");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(18))))==5e18,"partial global remainder");
  require(uint256(vm.load(EXCHANGE,userSlot(20)))==8453,"partial user head");
  require(uint256(vm.load(EXCHANGE,userSlot(21)))==8453,"partial user tail");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(nodeSlot(8453))+1)))==5e18,"partial node remainder");
 }
 function testSecondOpenCannotReuseQueueCredit() public {
  seedQueue(MARGIN);
  (bool ok1,bytes memory out1)=open(true,NONCE);
  require(ok1,"first debt open");
  vm.roll(block.number+1);vm.warp(block.timestamp+1);
  (bool ok2,bytes memory out2)=open(true,NONCE+1);
  require(!ok2 && errorIs(out2,0x8e667356),"second debt open rejected");
  uint256 a=abi.decode(out1,(uint256));
  require((positionWord(a)>>232)&0xff==1,"first debt flag");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(11))))==POSITION_ID+1,"next id unchanged");
  require(uint256(vm.load(EXCHANGE,userSlot(19)))==0,"user queue exhausted");
  require(uint256(vm.load(EXCHANGE,bytes32(uint256(18))))==0,"global queue exhausted");
 }
}
