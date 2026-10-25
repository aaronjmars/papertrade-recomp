pragma solidity ^0.8.24;

import "./Ledger.t.sol";

// Two queue-linkage experiments on the first older Exchange (earlier_1).
//
// LinkageTest builds the queue nodes with the linked library itself (a profitable
// plain close whose gain is deferred because the bankroll is forced to zero), then
// reads back the head, the tail and both node words. This is what the library
// actually creates; a hand-built list is not evidence about the library.
//
// NegativeControl builds the same two nodes by hand, with the `next` pointer running
// from the newer node to the older one (the reverse of the library's convention), and
// shows what an inconsistent linkage does to the debt-funded open's consumption. The
// contrast is the control for the "multi-node credit is consumed exactly" row.

contract LinkageTest is LedgerTest {
    function testLibraryCreatedLinkage() public {
        makeLibraryNode(3000000);
        uint256 n1 = uint256(vm.load(EXCHANGE, bytes32(uint256(16))));
        note("n1_node", n1);
        note("n1_userQueued", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("n1_userHead", uint256(vm.load(EXCHANGE, userSlot(20))));
        note("n1_userTail", uint256(vm.load(EXCHANGE, userSlot(21))));
        note("n1_nodeWord0_lo", uint256(vm.load(EXCHANGE, nodeSlot(n1))) & ((uint256(1) << 160) - 1));
        note("n1_nodeWord0_hi", uint256(vm.load(EXCHANGE, nodeSlot(n1))) >> 160);
        note("n1_nodeAmount", uint256(vm.load(EXCHANGE, bytes32(uint256(nodeSlot(n1)) + 1))));
        note("n1_nextCounter", uint256(vm.load(EXCHANGE, bytes32(uint256(17)))));
        vm.roll(block.number + 1);
        vm.warp(block.timestamp + 1);
        makeLibraryNode(3000100);
        uint256 n2 = uint256(vm.load(EXCHANGE, userSlot(21)));
        note("n2_node", n2);
        note("n2_userQueued", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("n2_globalQueued", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        note("n2_userHead", uint256(vm.load(EXCHANGE, userSlot(20))));
        note("n2_userTail", uint256(vm.load(EXCHANGE, userSlot(21))));
        note("n2_globalHead", uint256(vm.load(EXCHANGE, bytes32(uint256(16)))));
        note("n2_node1Word0_hi", uint256(vm.load(EXCHANGE, nodeSlot(n1))) >> 160);
        note("n2_node2Word0_hi", uint256(vm.load(EXCHANGE, nodeSlot(n2))) >> 184);
        vm.writeFile("out/linkage.txt", acc);
    }
}

contract NegativeControl is LedgerTest {
    /// @dev hand-built two-node list with the reverse linkage
    function seedReversedTwoNodes(uint256 a, uint256 b) internal {
        uint256 node = uint256(vm.load(EXCHANGE, bytes32(uint256(17))));
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(16)))) == node, "queue head base");
        require(uint256(vm.load(EXCHANGE, bytes32(uint256(18)))) == 0, "empty global queue");
        vm.store(EXCHANGE, bytes32(uint256(17)), bytes32(node + 2));
        vm.store(EXCHANGE, bytes32(uint256(18)), bytes32(a + b));
        vm.store(EXCHANGE, userSlot(19), bytes32(a + b));
        vm.store(EXCHANGE, userSlot(20), bytes32(node));
        vm.store(EXCHANGE, userSlot(21), bytes32(node + 1));
        // node is the head, node+1 the tail; the tail keeps the only pointer
        vm.store(EXCHANGE, nodeSlot(node), bytes32(uint256(uint160(USER))));
        vm.store(EXCHANGE, bytes32(uint256(nodeSlot(node)) + 1), bytes32(a));
        vm.store(EXCHANGE, nodeSlot(node + 1), bytes32(uint256(uint160(USER))));
        vm.store(EXCHANGE, bytes32(uint256(nodeSlot(node + 1)) + 1), bytes32(b));
    }

    function testReversedLinkageUnderConsumes() public {
        seedReversedTwoNodes(25e18, 10e18);
        note("pre_userQueued", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("pre_userHead", uint256(vm.load(EXCHANGE, userSlot(20))));
        note("pre_userTail", uint256(vm.load(EXCHANGE, userSlot(21))));
        (bool ok,) = openPos(true, MARGIN, 4000000);
        note("open_ok", ok ? 1 : 0);
        note("post_userQueued", uint256(vm.load(EXCHANGE, userSlot(19))));
        note("post_global", uint256(vm.load(EXCHANGE, bytes32(uint256(18)))));
        note("post_userHead", uint256(vm.load(EXCHANGE, userSlot(20))));
        note("post_userTail", uint256(vm.load(EXCHANGE, userSlot(21))));
        note("post_head_amount", uint256(vm.load(EXCHANGE, bytes32(uint256(nodeSlot(uint256(vm.load(EXCHANGE, bytes32(uint256(16)))))) + 1))));
        vm.writeFile("out/negative_control_reversed_linkage.txt", acc);
    }
}