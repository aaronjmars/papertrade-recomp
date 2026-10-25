pragma solidity ^0.8.24;

import "./DebtOpen.t.sol";

contract OlderSettlementExchangeTest is DebtOpenTest {
    uint256 constant GAIN = 331156061910525405;
    uint256 constant GAIN_FEE = 6623121238210508;
    event TightClose(uint256 available, uint256 credited, uint256 queued, uint256 feeWordBefore, uint256 feeWordAfter);

    function available() internal view returns (uint256) {
        (bool ok, bytes memory out) = EXCHANGE.staticcall(hex"0cdd5fc4");
        require(ok && out.length == 32, "available getter");
        return abi.decode(out, (uint256));
    }

    function checkTight(uint256 targetAvailable, uint256 expectedCredit, uint256 expectedQueue) internal {
        (bool opened,) = open(false, NONCE);
        require(opened, "signed open");
        vm.etch(BBO, address(new CoreBboLower()).code);
        uint256 originalAvailable = available();
        uint256 originalTreasury = uint256(vm.load(EXCHANGE, bytes32(uint256(14))));
        uint256 beforeBalance = uint256(vm.load(EXCHANGE, userSlot(9)));
        uint256 feeWordBefore = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        require(originalTreasury >= originalAvailable, "treasury reserve");
        vm.store(EXCHANGE, bytes32(uint256(14)), bytes32(originalTreasury - originalAvailable + targetAvailable));
        require(available() == targetAvailable, "target LP availability");
        (bool closed,) = closeOne(POSITION_ID, NONCE + 1);
        require(closed, "signed close");
        uint256 queued = uint256(vm.load(EXCHANGE, userSlot(19)));
        uint256 afterBalance = uint256(vm.load(EXCHANGE, userSlot(9)));
        uint256 feeWordAfter = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        require(queued == expectedQueue, "queued gain");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(18)))) == expectedQueue, "global queue");
        require(afterBalance - beforeBalance == MARGIN + expectedCredit, "credited gain and margin");
        uint256 expectedFee = GAIN - expectedCredit - expectedQueue;
        uint256 lowMask = type(uint128).max;
        require((feeWordAfter & lowMask) - (feeWordBefore & lowMask) == expectedFee / 2, "staker fee");
        require((feeWordAfter >> 128) - (feeWordBefore >> 128) == expectedFee - expectedFee / 2, "dev fee");
        emit TightClose(targetAvailable, expectedCredit, queued, feeWordBefore, feeWordAfter);
    }

    function testTightZeroQueuesGain() public {
        checkTight(0, 0, GAIN);
    }
    function testTightPartialQueuesRemainder() public {
        checkTight(GAIN - 1, GAIN - 1, 1);
    }
    function testTightExactGainPaysWithoutFee() public {
        checkTight(GAIN, GAIN, 0);
    }
    function testTightBelowFeeThresholdPaysWithoutFee() public {
        checkTight(GAIN + GAIN_FEE - 1, GAIN, 0);
    }
    function testTightAtFeeThresholdPaysFee() public {
        checkTight(GAIN + GAIN_FEE, GAIN - GAIN_FEE, 0);
    }
}
