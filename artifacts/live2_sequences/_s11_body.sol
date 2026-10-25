// s11: the debt-funded open. A queued claim funds the margin, then the position is closed at
// the same quote and the cycle is repeated with the same queued credit.
    function test_s11_debt_cycle() public {
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        creditUser(1000000 * WAD);
        uint256 a = openPosition(true, 5000 * WAD, 100, 2000, false, "s11", "open_a");
        fixtureAvail(0, "s11", "fixture_avail_zero");
        mockBbo(INST, uint64(ENTRY_PRICE_V + 995), uint64(ENTRY_PRICE_V + 1005));
        closeAndLog(one(a), 2001, "s11", "close_a_win_queued");
        step("s11", "queue_state", true, "", queueState());
        // cycle 1
        uint256 d1 = openDebt(1000 * WAD, 100, 2002, "s11", "cycle1_open_debt_1000");
        step("s11", "cycle1_after_open", true, "", queueState());
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        closeDebt(d1, 2003, "s11", "cycle1_close_debt_same_quote");
        step("s11", "cycle1_after_close", true, "", queueState());
        fixtureAvail(BIG, "s11", "cycle1_fixture_avail_big");
        harvestAndLog(10, "s11", "cycle1_harvest");
        step("s11", "cycle1_after_harvest", true, "", queueState());
        // cycle 2 with the same queued credit
        uint256 d2 = openDebt(1000 * WAD, 100, 2004, "s11", "cycle2_open_debt_1000");
        step("s11", "cycle2_after_open", true, "", queueState());
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        closeDebt(d2, 2005, "s11", "cycle2_close_debt_same_quote");
        step("s11", "cycle2_after_close", true, "", queueState());
        harvestAndLog(10, "s11", "cycle2_harvest");
        step("s11", "cycle2_after_harvest", true, "", queueState());
        // a third cycle at a larger margin, bounded by the queued credit
        uint256 d3 = openDebt(1634 * WAD, 100, 2006, "s11", "cycle3_open_debt_1634");
        mockBbo(INST, uint64(ENTRY_PRICE_V - 5), uint64(ENTRY_PRICE_V + 5));
        closeDebt(d3, 2007, "s11", "cycle3_close_debt_same_quote");
        harvestAndLog(10, "s11", "cycle3_harvest");
        step("s11", "cycle3_after_harvest", true, "", queueState());
        // and a debt position taken to liquidation instead of a close
        uint256 d4 = openDebt(1000 * WAD, 100, 2008, "s11", "cycle4_open_debt_for_liquidation");
        mockBbo(INST, uint64(248000), uint64(248010));
        liquidateAndLog(one(d4), "s11", "cycle4_liquidate_debt_position");
        step("s11", "cycle4_after_liquidation", true, "", queueState());
        fixtureAvail(BIG, "s11", "cycle4_fixture_avail_big");
        harvestAndLog(10, "s11", "cycle4_harvest");
        step("s11", "end_state", true, "", queueState());