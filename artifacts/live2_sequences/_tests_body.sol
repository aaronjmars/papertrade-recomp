// s0: the invariant holds on the loaded prestate, and the checker detects a break.
    function test_s0_control_and_negative() public {
        step("s0", "load", true, "", "residual_expected=0");
        writeUnfundedPosition(900001, 20000 * WAD, 500, ENTRY_PRICE_V);
        step("s0", "unfunded_position_negative_control", true, "", "margin_expected_in_residual=20000000000000000000000");
    }

    // s1: open then close at the same quote, five times, from the venue's own opens.
    function test_s1_open_close_same_price_cycles() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        step("s1", "deposit_credit", true, "", note2("credit", 1000000 * WAD));
        for (uint256 cycle; cycle < 5; cycle++) {
            uint256 id = openPosition(true, 5000 * WAD, 100, uint64(1000 + cycle), false,
                                      "s1", cycle == 0 ? "open_0" : "open_n");
            if (id == type(uint256).max) continue;
            closeAndLog(one(id), uint64(2000 + cycle), "s1", cycle == 0 ? "close_same_price_0" : "close_same_price_n");
        }
        step("s1", "final_claim", true, "", string.concat("balance=", u2s(userBalance()), ",locked=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_BALANCES))) >> 128))));
    }

    // s2: a solvent win then a loss, from the venue's own opens (fee, LP debit and mint accounting).
    function test_s2_win_then_loss() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        forceAvail(BIG);
        creditUser(1000000 * WAD);
        uint256 win = openPosition(true, 5000 * WAD, 100, 1100, false, "s2", "open_win");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(win), 1101, "s2", "close_win_solvent");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        uint256 loss = openPosition(true, 5000 * WAD, 100, 1102, false, "s2", "open_loss");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 1005), uint64(ENTRY_PRICE_V - 995));
        closeAndLog(one(loss), 1103, "s2", "close_loss");
        step("s2", "after", true, "", note2("paper_supply", paperSupply()));
    }

    // s3: open then liquidate at the maintenance boundary, LP bankroll funded.
    function test_s3_open_then_liquidate() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
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
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 q = openPosition(true, 5000 * WAD, 100, 1300, false, "s4", "open_queued_win");
        uint256 l = openPosition(true, 5000 * WAD, 100, 1301, false, "s4", "open_to_liquidate");
        forceAvail(0);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(q), 1302, "s4", "close_win_queued");
        step("s4", "queue_live", true, "", string.concat("queued=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_QUEUED))))), ",avail=", u2s(bankroll())));
        mockBbo(INST, uint64(248000), uint64(248010));
        liquidateAndLog(one(l), "s4", "liquidate_while_queue_live");
        forceAvail(BIG);
        harvestAndLog(10, "s4", "harvest");
        harvestAndLog(10, "s4", "harvest_again");
    }

    // s5: a deferred win, then a funded harvest, then a second harvest.
    function test_s5_queued_win_then_harvest() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 id = openPosition(true, 5000 * WAD, 100, 1400, false, "s5", "open");
        forceAvail(0);
        step("s5", "avail_zero", true, "", "lpBankrollAvailable=0");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(id), 1401, "s5", "close_win_queued");
        forceAvail(BIG);
        step("s5", "avail_restored", true, "", "lpBankrollAvailable=big");
        harvestAndLog(10, "s5", "harvest_1");
        harvestAndLog(10, "s5", "harvest_2");
    }

    // s6: a legitimate loss while the queue is live, then a winner into the live queue.
    function test_s6_loss_into_live_queue_then_win() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 fill = openPosition(true, 5000 * WAD, 100, 1500, false, "s6", "open_fill_win");
        uint256 a = openPosition(true, 5000 * WAD, 100, 1501, false, "s6", "open_a");
        uint256 b = openPosition(true, 5000 * WAD, 100, 1502, false, "s6", "open_b");
        forceAvail(0);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(fill), 1503, "s6", "close_fill_win_queued");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 1005), uint64(ENTRY_PRICE_V - 995));
        closeAndLog(one(a), 1504, "s6", "close_a_loss_while_queued");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(b), 1505, "s6", "close_b_win_into_live_queue");
        forceAvail(BIG);
        harvestAndLog(10, "s6", "harvest");
        harvestAndLog(10, "s6", "harvest_again");
    }

    // s7: both sides of one market in one block, closed in two orders.
    function test_s7_both_sides_one_market() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 lng = openPosition(true, 5000 * WAD, 100, 1600, false, "s7", "open_long");
        uint256 sht = openPosition(false, 5000 * WAD, 100, 1601, false, "s7", "open_short");
        uint256[] memory both = new uint256[](2);
        both[0] = lng; both[1] = sht;
        closeAndLog(both, 1602, "s7", "close_both_one_batch");
        uint256 lng2 = openPosition(true, 5000 * WAD, 100, 1603, false, "s7", "open_long_2");
        uint256 sht2 = openPosition(false, 5000 * WAD, 100, 1604, false, "s7", "open_short_2");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 495), uint64(ENTRY_PRICE_V + 505));
        closeAndLog(one(lng2), 1605, "s7", "close_winner_first");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 505), uint64(ENTRY_PRICE_V - 495));
        closeAndLog(one(sht2), 1606, "s7", "close_loser_second");
    }

    // s8: dust margin, the deadband boundary, the leverage bound and the per-side cap.
    function test_s8_boundaries() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 dust = openPosition(true, 1, 1, 1700, false, "s8", "open_one_wei");
        closeAndLog(one(dust), 1701, "s8", "close_one_wei_same_quote");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 5), uint64(ENTRY_PRICE_V + 6));
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
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 id = openPosition(true, 5000 * WAD, 100, 1800, false, "s9", "open");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(id), 1801, "s9", "close_win");
        mockStatus(1);
        step("s9", "status_true", true, "", "mock 0x0810 returns 1");
        withdrawAndLog(2_000_000, 1802, "s9", "withdraw_status_true");
        mockStatus(0);
        step("s9", "status_false", true, "", "mock 0x0810 returns 0");
        withdrawAndLog(2_000_000, 1803, "s9", "withdraw_status_false");
    }

    // s10: two closes in one BatchExecutor transaction, through the real allowlist.
    function test_s10_batch_executor_two_closes() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 a = openPosition(true, 5000 * WAD, 100, 1900, false, "s10", "open_a");
        uint256 b = openPosition(false, 5000 * WAD, 100, 1901, false, "s10", "open_b");
        registerSession(PK);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 495), uint64(ENTRY_PRICE_V + 505));
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

    // s11: a debt-funded open against a real queued claim, then harvest.
    function test_s11_debt_open_against_queue() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 a = openPosition(true, 5000 * WAD, 100, 2000, false, "s11", "open_a");
        forceAvail(0);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(a), 2001, "s11", "close_win_queued");
        step("s11", "before_debt_open", true, "", string.concat("queued=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_QUEUED))))), ",user_queued=",
            u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(19)))))), ",bal=", u2s(userBalance())));
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        uint256 b = openPosition(true, 1000 * WAD, 100, 2002, true, "s11", "open_use_debt");
        step("s11", "after_debt_open", true, "", string.concat("queued=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_QUEUED))))), ",user_queued=",
            u2s(uint256(vm.load(EXCHANGE, keccak256(abi.encode(USER, uint256(19)))))), ",bal=", u2s(userBalance())));
        forceAvail(BIG);
        if (b != type(uint256).max) closeAndLog(one(b), 2003, "s11", "close_b");
        harvestAndLog(10, "s11", "harvest");
        harvestAndLog(10, "s11", "harvest_again");
    }

    // s12: the LP surplus path with the LP cursor below its cap and negative.
    function test_s12_push_staker_fees_below_cap() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        forceAvail(0);
        step("s12", "lp_at_zero", true, "", "trackedLP=0");
        uint256 id = openPosition(true, 5000 * WAD, 100, 2100, false, "s12", "open");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(id), 2101, "s12", "close_win_queued");
        step("s12", "lp_negative", true, "", string.concat("trackedLP=",
            vm.toString(vm.load(TOKENOMICS, bytes32(uint256(3))))));
        pushStakerFeesAndLog("s12", "push_stranger_lp_negative");
        pushStakerFeesAndLog("s12", "push_stranger_lp_negative_again");
    }

    // s13: the LP surplus path above the cap, twice, and with a live queue.
    function test_s13_push_staker_fees_above_cap() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        forceAvail(5000000 * WAD + 1000 * WAD);
        step("s13", "lp_above_cap", true, "", "trackedLP=5001000e18");
        pushStakerFeesAndLog("s13", "push_stranger_above_cap_1");
        pushStakerFeesAndLog("s13", "push_stranger_above_cap_2");
        uint256 a = openPosition(true, 5000 * WAD, 100, 2200, false, "s13", "open_a");
        uint256 b = openPosition(true, 5000 * WAD, 100, 2201, false, "s13", "open_b");
        forceAvail(5000000 * WAD + 1000 * WAD);
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(a), 2202, "s13", "close_win_queued");
        step("s13", "queue_live_with_excess", true, "", string.concat("queued=",
            u2s(uint256(vm.load(EXCHANGE, bytes32(uint256(SLOT_TOTAL_QUEUED))))), ",trackedLP=",
            vm.toString(vm.load(TOKENOMICS, bytes32(uint256(3))))));
        pushStakerFeesAndLog("s13", "push_with_live_queue");
        pushStakerFeesAndLog("s13", "push_with_live_queue_again");
        forceAvail(BIG);
        harvestAndLog(10, "s13", "harvest");
        if (b != type(uint256).max) closeAndLog(one(b), 2203, "s13", "close_b");
    }