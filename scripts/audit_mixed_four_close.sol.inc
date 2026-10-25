    struct MixedState {
        uint256[] ids;
        uint256 totalMargin;
        uint256 oldTotals;
        uint256 oldLocked;
        uint256 oldBalance;
        uint256 oldFees;
        uint256 oldQueue;
    }

    function prepareMixedPositions(bool gainFirst) internal returns (MixedState memory state) {
        bytes32 gainSlot = positionSlot(1392206);
        bytes32 lossSlot = positionSlot(1392921);
        uint256 gainWord0 = uint256(vm.load(EXCHANGE, gainSlot));
        uint256 gainWord1 = uint256(vm.load(EXCHANGE, bytes32(uint256(gainSlot) + 1)));
        uint256 lossWord0 = uint256(vm.load(EXCHANGE, lossSlot));
        uint256 lossWord1 = uint256(vm.load(EXCHANGE, bytes32(uint256(lossSlot) + 1)));
        require((gainWord1 & (uint256(1) << 240)) != 0, "gain template active");
        require((lossWord1 & (uint256(1) << 240)) != 0, "loss template active");
        require((gainWord0 >> 160) & type(uint32).max ==
                (lossWord0 >> 160) & type(uint32).max, "same market templates");
        require(gainWord0 >> 192 < 808455 && lossWord0 >> 192 > 808455,
                "opposite historical PnL signs");
        state.ids = new uint256[](4);
        uint256 gainMargin = uint128(gainWord1);
        uint256 lossMargin = uint128(lossWord1);
        state.totalMargin = 2 * (gainMargin + lossMargin);
        for (uint256 i; i < 4; ++i) {
            state.ids[i] = i + 1;
            bytes32 slot = positionSlot(state.ids[i]);
            uint256 word0 = (i % 2 == 0) == gainFirst ? gainWord0 : lossWord0;
            uint256 word1 = (i % 2 == 0) == gainFirst ? gainWord1 : lossWord1;
            vm.store(EXCHANGE, slot,
                     bytes32((word0 & ~uint256(type(uint160).max)) | uint160(USER)));
            vm.store(EXCHANGE, bytes32(uint256(slot) + 1), bytes32(word1));
        }
        state.oldTotals = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        state.oldLocked = state.oldTotals >> 128;
        require(state.oldLocked + state.totalMargin < 2**128, "locked margin range");
        vm.store(EXCHANGE, bytes32(uint256(22)),
                 bytes32(((state.oldLocked + state.totalMargin) << 128) |
                         uint128(state.oldTotals)));
        state.oldBalance = uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(9)))));
        state.oldFees = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        state.oldQueue = uint256(vm.load(EXCHANGE, bytes32(uint256(18))));
    }

    function executeMixedClose(uint256[] memory ids) internal returns (Vm.Log[] memory logs) {
        address sessionKey = vm.addr(0xb0b);
        bytes32 outer = keccak256(abi.encode(USER, uint256(4)));
        vm.store(SESSION, keccak256(abi.encode(sessionKey, outer)),
                 bytes32(uint256(block.timestamp + 3600)));
        uint64 deadline = uint64(block.timestamp + 3600);
        bytes32 structHash = keccak256(abi.encode(CLOSE_TYPEHASH, USER,
            keccak256(abi.encodePacked(ids)), NONCE, deadline));
        bytes32 digest = keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
        (uint8 v, bytes32 r, bytes32 sigS) = vm.sign(0xb0b, digest);
        require(ecrecover(digest, v, r, sigS) == sessionKey, "session signer");
        vm.recordLogs();
        vm.prank(BATCH);
        (bool ok, bytes memory result) = EXCHANGE.call(abi.encodeWithSelector(
            bytes4(0x2792e706), USER, ids, NONCE, deadline, v, r, sigS));
        if (!ok) revert WrongResult(ok, result);
        return vm.getRecordedLogs();
    }

    struct MixedOutcome {
        int256 expectedBalanceDelta;
        uint256 eventFees;
        uint256 summaryDelta;
        uint256 summaryAfter;
        uint256 summaryFees;
    }

    function readMixedEvents(Vm.Log[] memory logs, uint256[] memory ids,
                             uint256 totalMargin) internal pure
        returns (MixedOutcome memory outcome)
    {
        uint256 closed;
        uint256 positives;
        uint256 negatives;
        uint256 summaries;
        outcome.expectedBalanceDelta = int256(totalMargin);
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].emitter != EXCHANGE || logs[i].topics.length == 0) continue;
            if (logs[i].topics[0] ==
                0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf) {
                require(closed < 4 && uint256(logs[i].topics[1]) == ids[closed],
                        "position order");
                require(address(uint160(uint256(logs[i].topics[2]))) == USER,
                        "position user");
                (, , int256 adjustedPnl, , uint256 fee) = abi.decode(logs[i].data,
                    (uint256, int256, int256, uint256, uint256));
                if (adjustedPnl > 0) {
                    ++positives;
                    outcome.expectedBalanceDelta += adjustedPnl - int256(fee);
                } else if (adjustedPnl < 0) {
                    ++negatives;
                    outcome.expectedBalanceDelta += adjustedPnl;
                }
                outcome.eventFees += fee;
                ++closed;
            } else if (logs[i].topics[0] ==
                0xa32e4800a59f03b131f5fea90951bdf00d8d505ad98f48ece29d8620a0bf09b0) {
                require(address(uint160(uint256(logs[i].topics[1]))) == USER,
                        "summary user");
                (uint256 delta, uint256 balanceAfter, uint256 stakerFee, uint256 devFee) =
                    abi.decode(logs[i].data, (uint256, uint256, uint256, uint256));
                outcome.summaryDelta = delta;
                outcome.summaryAfter = balanceAfter;
                outcome.summaryFees = stakerFee + devFee;
                ++summaries;
            }
        }
        require(closed == 4 && positives == 2 && negatives == 2, "mixed PnL paths");
        require(summaries == 1, "one aggregate summary");
    }

    function assertMixedState(MixedState memory state, MixedOutcome memory outcome)
        internal view
    {
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(18)))) == state.oldQueue,
                "queue unchanged");
        uint256 newTotals = uint256(vm.load(EXCHANGE, bytes32(uint256(22))));
        require(newTotals >> 128 == state.oldLocked, "four margins released");
        uint256 newBalance = uint256(vm.load(EXCHANGE,
            keccak256(abi.encode(USER, uint256(9)))));
        require(int256(newBalance) - int256(state.oldBalance) ==
                outcome.expectedBalanceDelta, "mixed balance equation");
        require(newBalance - state.oldBalance == outcome.summaryDelta &&
                outcome.summaryAfter == newBalance, "aggregate summary balance");
        require(uint128(newTotals) - uint128(state.oldTotals) == outcome.summaryDelta,
                "total balance equation");
        uint256 newFees = uint256(vm.load(EXCHANGE, bytes32(uint256(26))));
        uint256 feeDelta = (uint128(newFees) - uint128(state.oldFees)) +
            ((newFees >> 128) - (state.oldFees >> 128));
        require(feeDelta == outcome.eventFees &&
                outcome.summaryFees == outcome.eventFees, "mixed fee equation");
        for (uint256 i; i < 4; ++i) {
            bytes32 slot = positionSlot(state.ids[i]);
            require((uint256(vm.load(EXCHANGE, bytes32(uint256(slot) + 1))) &
                     (uint256(1) << 240)) == 0, "active position cleared");
        }
        bytes32 nonceOuter = keccak256(abi.encode(USER, uint256(6)));
        bytes32 nonceBitSlot = keccak256(abi.encode(uint256(0), nonceOuter));
        require(uint256(vm.load(SESSION, nonceBitSlot)) == uint256(1) << NONCE,
                "nonce bit persisted");
        require(uint256(vm.load(SESSION, keccak256(abi.encode(USER, uint256(5))))) ==
                NONCE + 1, "nonce counter persisted");
    }

    function testFourMixedPnlActivePositionsClose() public {
        runMixedPnlClose(true);
    }

    function testFourMixedPnlLossFirstClose() public {
        runMixedPnlClose(false);
    }

    function runMixedPnlClose(bool gainFirst) internal {
        MixedState memory state = prepareMixedPositions(gainFirst);
        Vm.Log[] memory logs = executeMixedClose(state.ids);
        MixedOutcome memory outcome = readMixedEvents(logs, state.ids, state.totalMargin);
        assertMixedState(state, outcome);
    }

    function writeCrossPosition(uint256 id, uint256 word0, uint256 word1) internal {
        bytes32 slot = positionSlot(id);
        vm.store(EXCHANGE, slot, bytes32((word0 & ~uint256(type(uint160).max)) | uint160(USER)));
        vm.store(EXCHANGE, bytes32(uint256(slot) + 1), bytes32(word1));
    }

    function prepareCrossMarketPositions(bool market0First) internal returns (MixedState memory state) {
        state = prepareMixedPositions(true);
        uint256[8] memory sourceWords;
        bytes32 market0GainSlot = positionSlot(1392206);
        bytes32 market0LossSlot = positionSlot(1392921);
        sourceWords[0] = uint256(vm.load(EXCHANGE, market0GainSlot));
        sourceWords[1] = uint256(vm.load(EXCHANGE, bytes32(uint256(market0GainSlot) + 1)));
        sourceWords[2] = uint256(vm.load(EXCHANGE, market0LossSlot));
        sourceWords[3] = uint256(vm.load(EXCHANGE, bytes32(uint256(market0LossSlot) + 1)));
        sourceWords[4] = uint256(__POSITION_1394058_WORD0__);
        sourceWords[5] = uint256(__POSITION_1394058_WORD1__);
        sourceWords[6] = uint256(__POSITION_1394060_WORD0__);
        sourceWords[7] = uint256(__POSITION_1394060_WORD1__);
        require((sourceWords[4] >> 160) & type(uint32).max == 1 &&
                (sourceWords[6] >> 160) & type(uint32).max == 1, "market-1 templates");
        require((sourceWords[5] >> 240) & 1 == 1 && (sourceWords[7] >> 240) & 1 == 1,
                "market-1 positions active");
        state.totalMargin = uint128(sourceWords[1]) + uint128(sourceWords[3]) +
                            uint128(sourceWords[5]) + uint128(sourceWords[7]);
        require(state.oldLocked + state.totalMargin < 2**128, "cross-market locked range");
        vm.store(EXCHANGE, bytes32(uint256(22)),
                 bytes32(((state.oldLocked + state.totalMargin) << 128) |
                         uint128(state.oldTotals)));
        uint256[4] memory order;
        if (market0First) order = [uint256(0), 2, 1, 3];
        else order = [uint256(2), 0, 3, 1];
        for (uint256 i; i < 4; ++i)
            writeCrossPosition(state.ids[i], sourceWords[2 * order[i]],
                               sourceWords[2 * order[i] + 1]);
        uint256 marketRoot = uint256(__MARKET1_CONFIG_ROOT__);
        vm.store(EXCHANGE, bytes32(marketRoot), __MARKET1_CONFIG_0__);
        vm.store(EXCHANGE, bytes32(marketRoot + 1), __MARKET1_CONFIG_1__);
        vm.store(EXCHANGE, bytes32(marketRoot + 2), __MARKET1_CONFIG_2__);
        uint256 fieldsRoot = uint256(__MARKET1_FIELDS_ROOT__);
        vm.store(EXCHANGE, bytes32(fieldsRoot), __MARKET1_FIELDS_0__);
        vm.store(EXCHANGE, bytes32(fieldsRoot + 1), __MARKET1_FIELDS_1__);
        address bbo = address(uint160(uint256(0x080e)));
        vm.mockCall(bbo, abi.encode(uint32(0)), abi.encode(uint256(808450), uint256(808460)));
        vm.mockCall(bbo, abi.encode(uint32(1)), abi.encode(uint256(234895), uint256(234905)));
    }

    function expectedCrossRawPnl(uint256 word0, uint256 word1, uint256 exitPrice)
        internal pure returns (int256)
    {
        uint256 entryPrice = word0 >> 192;
        uint256 leverage = (word1 >> 128) & type(uint32).max;
        bool isLong = ((word1 >> 224) & 1) == 1;
        int256 move = isLong ? int256(exitPrice) - int256(entryPrice) :
                               int256(entryPrice) - int256(exitPrice);
        if (move > 0) {
            int256 spread = int256(entryPrice / 50000);
            move = move > spread ? move - spread : int256(0);
        }
        uint256 magnitude = uint128(word1) * leverage * uint256(move < 0 ? -move : move)
                            / entryPrice;
        return move < 0 ? -int256(magnitude) : int256(magnitude);
    }

    function assertCrossMarketEvents(Vm.Log[] memory logs, uint256[] memory ids,
                                     bool market0First) internal view
    {
        uint256 closed;
        uint256 market0Count;
        uint256 market1Count;
        for (uint256 i; i < logs.length; ++i) {
            if (logs[i].emitter != EXCHANGE || logs[i].topics.length == 0 ||
                logs[i].topics[0] !=
                    0x87902ed2451849f465fc4d36a01d7f5c67b53af12f63ee85d2814a2d582f89bf)
                continue;
            require(closed < 4 && uint256(logs[i].topics[1]) == ids[closed],
                    "cross-market event order");
            bytes32 slot = positionSlot(ids[closed]);
            uint256 word0 = uint256(vm.load(EXCHANGE, slot));
            uint256 word1 = uint256(vm.load(EXCHANGE, bytes32(uint256(slot) + 1)));
            uint256 market = (word0 >> 160) & type(uint32).max;
            bool expectedMarket0 = (closed % 2 == 0) == market0First;
            require(market == (expectedMarket0 ? 0 : 1), "cross-market order");
            uint256 expectedExit = expectedMarket0 ? 808455 : 234900;
            (uint256 exitPrice, int256 rawPnl, int256 adjustedPnl, , ) =
                abi.decode(logs[i].data, (uint256, int256, int256, uint256, uint256));
            bool expectedGain = market0First ? (closed == 0 || closed == 3) :
                                             (closed == 1 || closed == 2);
            require((adjustedPnl > 0) == expectedGain &&
                    (adjustedPnl < 0) != expectedGain, "per-market PnL signs");
            require(exitPrice == expectedExit, "per-market BBO midpoint");
            require(rawPnl == expectedCrossRawPnl(word0, word1, exitPrice),
                    "independent raw PnL equation");
            if (expectedMarket0) ++market0Count;
            else ++market1Count;
            ++closed;
        }
        require(closed == 4 && market0Count == 2 && market1Count == 2,
                "two closes per market");
    }

    function testFourCrossMarketZeroFirstClose() public {
        runCrossMarketClose(true);
    }

    function testFourCrossMarketOneFirstClose() public {
        runCrossMarketClose(false);
    }

    function runCrossMarketClose(bool market0First) internal {
        MixedState memory state = prepareCrossMarketPositions(market0First);
        Vm.Log[] memory logs = executeMixedClose(state.ids);
        MixedOutcome memory outcome = readMixedEvents(logs, state.ids, state.totalMargin);
        assertMixedState(state, outcome);
        assertCrossMarketEvents(logs, state.ids, market0First);
    }
