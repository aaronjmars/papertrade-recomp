// SPDX-License-Identifier: MIT
pragma solidity >=0.8.0;

/// @title            Decompiled Contract
/// @author           Jonathan Becker <jonathan@jbecker.dev>
/// @custom:version   heimdall-rs v0.9.2
///
/// @notice           This contract was decompiled using the heimdall-rs decompiler.
///                     It was generated directly by tracing the EVM opcodes from this contract.
///                     As a result, it may not compile or even be valid solidity code.
///                     Despite this, it should be obvious what each function does. Overall
///                     logic should have been preserved throughout decompiling.
///
/// @custom:github    You can find the open-source decompiler here:
///                       https://heimdall.rs

contract DecompiledContract {
    bytes public constant unresolved_fe16eae8 = ;
    bytes public constant unresolved_db006a75 = ;
    
    uint256 public unresolved_cbb451da;
    uint256 public unresolved_dc5682d2;
    uint256 public unresolved_c16017ca;
    uint256 public unresolved_e9ed73e9;
    address public unresolved_8da5cb5b;
    uint256 public unresolved_ae745703;
    address public unresolved_d2f7265a;
    address public unresolved_98255e15;
    uint256 public unresolved_1c3972ba;
    
    event Event_09f6ca7b();
    event Event_4ffd725f();
    event Event_620c26bf();
    event Event_430bfdc2();
    event Event_3050fba1();
    event Event_dbf6f187();
    error CustomError_00000000();
    
    /// @custom:selector    0x12baae3b
    /// @custom:signature   Unresolved_12baae3b(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_12baae3b(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x80, CustomError_30cd7471());
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        require(arg0, CustomError_bad8ef95());
        require(arg1, CustomError_bad8ef95());
        require(arg2, CustomError_bad8ef95());
        require(arg3, CustomError_bad8ef95());
        require(arg1 < arg0, CustomError_bad8ef95());
        unresolved_e9ed73e9 = arg0;
        unresolved_c16017ca = arg1;
        unresolved_1c3972ba = arg2;
        unresolved_cbb451da = arg3;
        emit Event_dbf6f187(arg0, arg1, arg2, arg3);
        require(!arg3, CustomError_bad8ef95());
        unresolved_e9ed73e9 = arg0;
        unresolved_c16017ca = arg1;
        unresolved_1c3972ba = arg2;
        unresolved_cbb451da = arg3;
        emit Event_dbf6f187(arg0, arg1, arg2, arg3);
    }
    
    /// @custom:selector    0xc218c676
    /// @custom:signature   Unresolved_c218c676(uint256 arg0) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_c218c676(uint256 arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20, CustomError_e343677f());
        require(msg.sender - (address(unresolved_d2f7265a)), CustomError_e343677f());
        require(!arg0, CustomError_e247b81f());
        require(!(unresolved_ae745703 > unresolved_c16017ca), CustomError_e247b81f());
        require(((unresolved_ae745703 - unresolved_c16017ca) < unresolved_ae745703) & (0 > unresolved_c16017ca) | (((unresolved_ae745703 - unresolved_c16017ca) > unresolved_ae745703) & (!0 > unresolved_c16017ca)), CustomError_e247b81f());
        require(arg0 > (unresolved_ae745703 - unresolved_c16017ca), CustomError_e247b81f());
        require(((unresolved_ae745703 - arg0) < unresolved_ae745703) & (0 > arg0) | (((unresolved_ae745703 - arg0) > unresolved_ae745703) & (!0 > arg0)));
        unresolved_ae745703 = unresolved_ae745703 - arg0;
        emit Event_09f6ca7b(arg0, unresolved_ae745703 - arg0, unresolved_dc5682d2);
    }
    
    /// @custom:selector    0x7c7df7b4
    /// @custom:signature   Unresolved_7c7df7b4(address arg0, uint64 arg1, bool arg2) public pure
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg3 ["uint64", "bytes8", "int64"]
    /// @param              arg4 ["bool", "uint8", "bytes1", "int8"]
    function Unresolved_7c7df7b4(address arg0, uint64 arg1, bool arg2) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xe0);
        require(arg0 - (address(arg0)));
        require(uint64(arg3) - arg3);
        require(bytes1(arg4) - arg4);
    }
    
    /// @custom:selector    0xed722c96
    /// @custom:signature   Unresolved_ed722c96(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_ed722c96(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x80);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_d2f7265a)), CustomError_e343677f());
        require(arg3 > arg2, CustomError_85c58396());
        require(arg1);
        require(((unresolved_ae745703 - arg1) < unresolved_ae745703) & (0 > arg1) | (((unresolved_ae745703 - arg1) > unresolved_ae745703) & (!0 > arg1)));
        unresolved_ae745703 = unresolved_ae745703 - arg1;
        require(!arg2);
        require((!unresolved_ae745703 < 0) & ((unresolved_ae745703 + arg3) < arg3) | ((unresolved_ae745703 < 0) & (!(unresolved_ae745703 + arg3) < arg3)));
        require(arg3);
        unresolved_ae745703 = unresolved_ae745703 + arg3;
        var_d = unresolved_ae745703;
        (bool success, bytes memory ret0) = address(0xe991817199363046da0a28da6fbad0284e4aa492).Unresolved_7aac24ba(var_d); // delegatecall
        require(0);
        require(unresolved_dc5682d2 > (unresolved_dc5682d2 + 0));
        unresolved_dc5682d2 = unresolved_dc5682d2 + 0;
        require(0);
        require(address(unresolved_98255e15));
        require(!address(unresolved_98255e15).code.length);
        address var_d = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_98255e15).Unresolved_40c10f19(var_d); // call
        emit Event_620c26bf(address(arg0), arg1, arg2, unresolved_ae745703, unresolved_ae745703 + arg3, 0, 0);
        require(var_o > 0xffffffffffffffff);
        var_o = var_o;
        emit Event_620c26bf(address(arg0), arg1, arg2, unresolved_ae745703, unresolved_ae745703 + arg3, 0, 0);
        emit Event_620c26bf(address(arg0), arg1, arg2, unresolved_ae745703, unresolved_ae745703 + arg3, 0, 0);
        require(0x40 > ret0.length);
        require(((var_o + 0x40) < var_o) | ((var_o + 0x40) > 0xffffffffffffffff));
        uint256 var_o = var_o + 0x40;
        require(((var_o + 0x40) - var_o) < 0x40);
        emit Event_620c26bf(address(arg0), arg1, 0, unresolved_ae745703, unresolved_ae745703, 0, 0);
    }
    
    /// @custom:selector    0x485cc955
    /// @custom:signature   Unresolved_485cc955(address arg0, address arg1) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_485cc955(address arg0, address arg1) public payable {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(bytes1(unresolved_8da5cb5b), CustomError_0dc149f0());
        require(!(bytes1(unresolved_8da5cb5b >> 0x08)), CustomError_0dc149f0());
        require(!(bytes1(unresolved_8da5cb5b >> 0x08)), CustomError_0dc149f0());
        unresolved_8da5cb5b = (uint96(unresolved_8da5cb5b)) | (address(arg0 << 0x10));
        unresolved_d2f7265a = (uint96(unresolved_d2f7265a)) | (address(arg1));
        unresolved_e9ed73e9 = 0x01a784379d99db42000000;
        unresolved_c16017ca = 0x0422ca8b0a00a425000000;
        unresolved_1c3972ba = 0x056bc75e2d63100000;
        unresolved_cbb451da = 0x6342fd08f00f6378000000;
        emit Event_4ffd725f(address(arg0));
        emit Event_dbf6f187(0x01a784379d99db42000000, 0x0422ca8b0a00a425000000, 0x056bc75e2d63100000, 0x6342fd08f00f6378000000);
        require(!(bytes1(unresolved_8da5cb5b >> 0x08)), CustomError_0dc149f0());
        unresolved_8da5cb5b = (uint88(unresolved_8da5cb5b)) | (address(arg0 << 0x10));
        require(bytes1(unresolved_8da5cb5b), CustomError_0dc149f0());
    }
    
    /// @custom:selector    0x0efdf838
    /// @custom:signature   Unresolved_0efdf838(address arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    function Unresolved_0efdf838(address arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg0 - (address(arg0)));
        require(arg2 - arg2);
        require(msg.sender - (address(unresolved_d2f7265a)), CustomError_e343677f());
        require(arg4 > arg3, CustomError_85c58396());
        require(!arg3);
        require((!unresolved_ae745703 < 0) & ((unresolved_ae745703 + arg4) < arg4) | ((unresolved_ae745703 < 0) & (!(unresolved_ae745703 + arg4) < arg4)));
        require(arg4);
        unresolved_ae745703 = unresolved_ae745703 + arg4;
        var_d = unresolved_ae745703;
        (bool success, bytes memory ret0) = address(0xe991817199363046da0a28da6fbad0284e4aa492).Unresolved_7aac24ba(var_d); // delegatecall
        require(0);
        require(unresolved_dc5682d2 > (unresolved_dc5682d2 + 0));
        unresolved_dc5682d2 = unresolved_dc5682d2 + 0;
        require(0);
        require(address(unresolved_98255e15));
        require(!address(unresolved_98255e15).code.length);
        address var_d = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_98255e15).Unresolved_40c10f19(var_d); // call
        emit Event_3050fba1(address(arg0), arg1, arg2, arg3, unresolved_ae745703, unresolved_ae745703 + arg4, 0, 0);
        require(var_o > 0xffffffffffffffff);
        var_o = var_o;
        emit Event_3050fba1(address(arg0), arg1, arg2, arg3, unresolved_ae745703, unresolved_ae745703 + arg4, 0, 0);
        emit Event_3050fba1(address(arg0), arg1, arg2, arg3, unresolved_ae745703, unresolved_ae745703 + arg4, 0, 0);
        require(0x40 > ret0.length);
        require(((var_o + 0x40) < var_o) | ((var_o + 0x40) > 0xffffffffffffffff));
        uint256 var_o = var_o + 0x40;
        require(((var_o + 0x40) - var_o) < 0x40);
    }
    
    /// @custom:selector    0xe6ee2285
    /// @custom:signature   Unresolved_e6ee2285(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_e6ee2285(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_98255e15 = (uint96(unresolved_98255e15)) | (address(arg0));
        emit Event_430bfdc2(address(arg0));
    }
    
    /// @custom:selector    0xf2fde38b
    /// @custom:signature   Unresolved_f2fde38b(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_f2fde38b(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_8da5cb5b = (address(arg0 << 0x10)) | (uint96(unresolved_8da5cb5b));
        emit Event_4ffd725f(address(arg0));
    }
}