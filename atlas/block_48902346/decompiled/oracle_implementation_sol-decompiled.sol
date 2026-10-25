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
    address public unresolved_8da5cb5b;
    
    event Event_4ffd725f();
    error CustomError_00000000();
    
    /// @custom:selector    0xa066fae9
    /// @custom:signature   Unresolved_a066fae9(uint32 arg0) public payable returns (uint64)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_a066fae9(uint32 arg0) public payable returns (uint64) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        var_b = 0x20;
        require(((var_c + 0x40) > 0xffffffffffffffff) | ((var_c + 0x40) < var_c), "Mark price read failed");
        uint256 var_c = var_c + 0x40;
        (bool success, bytes memory ret0) = address(0x0806).Unresolved_00000000(var_f); // staticcall
        require(!ret0.length, "Mark price read failed");
        require(((0x60 + var_k) - 0x60) < 0x20);
        require(var_b - (uint64(var_b)));
        require(!(uint64(var_b)), "Mark price is zero");
        return uint64(var_b);
        require(!(!var_k < 0x20), "Mark price read failed");
        require(ret0.length > 0xffffffffffffffff, "Mark price read failed");
        require(((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), "Mark price read failed");
    }
    
    /// @custom:selector    0xc4d66de8
    /// @custom:signature   Unresolved_c4d66de8(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_c4d66de8(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(bytes1(unresolved_8da5cb5b), CustomError_0dc149f0());
        require(!(bytes1(unresolved_8da5cb5b >> 0x08)), CustomError_0dc149f0());
        require(!(bytes1(unresolved_8da5cb5b >> 0x08)), CustomError_0dc149f0());
        unresolved_8da5cb5b = (address(arg0 << 0x10)) | (uint96(unresolved_8da5cb5b));
        emit Event_4ffd725f(address(arg0));
        require(!(bytes1(unresolved_8da5cb5b >> 0x08)), CustomError_0dc149f0());
        unresolved_8da5cb5b = uint248(unresolved_8da5cb5b);
        require(bytes1(unresolved_8da5cb5b), CustomError_0dc149f0());
    }
    
    /// @custom:selector    0x2af78bd1
    /// @custom:signature   Unresolved_2af78bd1(uint32 arg0) public payable returns (uint64)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_2af78bd1(uint32 arg0) public payable returns (uint64) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        var_b = 0x20;
        require(((var_c + 0x40) > 0xffffffffffffffff) | ((var_c + 0x40) < var_c), "Oracle read failed");
        uint256 var_c = var_c + 0x40;
        (bool success, bytes memory ret0) = address(0x0807).Unresolved_00000000(var_f); // staticcall
        require(!ret0.length, "Oracle read failed");
        require(((0x60 + var_k) - 0x60) < 0x20);
        require(var_b - (uint64(var_b)));
        require(!(uint64(var_b)), "Oracle price is zero");
        return uint64(var_b);
        require(!(!var_k < 0x20), "Oracle read failed");
        require(ret0.length > 0xffffffffffffffff, "Oracle read failed");
        require(((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), "Oracle read failed");
    }
    
    /// @custom:selector    0x766cd255
    /// @custom:signature   Unresolved_766cd255(uint32 arg0) public payable
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_766cd255(uint32 arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        require(((var_a + 0xa0) < var_a) | ((var_a + 0xa0) > 0xffffffffffffffff), "Oracle read failed");
        uint256 var_a = var_a + 0xa0;
        uint256 var_d = 0;
        require(((var_a + 0xa0) < var_a) | ((var_a + 0xa0) > 0xffffffffffffffff), "Oracle read failed");
        var_a = var_a + 0xa0;
        require(((var_a + 0x40) > 0xffffffffffffffff) | ((var_a + 0x40) < var_a), "Oracle read failed");
        var_a = var_a + 0x40;
        (bool success, bytes memory ret0) = address(0x0807).Unresolved_00000000(var_p); // staticcall
        require(!ret0.length, "Oracle read failed");
        require(((0x60 + var_u) - 0x60) < 0x20);
        require(var_d - (uint64(var_d)));
        require(!(uint64(var_d)), "Oracle price is zero");
        require(!(!var_u < 0x20), "Oracle read failed");
        require(ret0.length > 0xffffffffffffffff, "Oracle read failed");
        require(((var_a + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_a) | ((var_a + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), "Oracle read failed");
    }
    
    /// @custom:selector    0xa7f06462
    /// @custom:signature   Unresolved_a7f06462(uint256 arg0, uint32 arg1) public payable returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint32", "bytes4", "int32"]
    function Unresolved_a7f06462(uint256 arg0, uint32 arg1) public payable returns (bytes memory) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x20);
        require(arg0 > 0xffffffffffffffff);
        require(!(arg0 + 0x23) < msg.data.length);
        require(arg0  > 0xffffffffffffffff);
        require(((arg0 + (arg0  << 0x05)) + 0x24) > msg.data.length);
        require(arg0  > 0xffffffffffffffff);
        require(((var_c + (uint248((0x20 + (arg0  << 0x05)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (arg0  << 0x05)) + 0x1f))) > 0xffffffffffffffff));
        uint256 var_c = var_c + (uint248((0x20 + (arg0  << 0x05)) + 0x1f));
        uint256 var_d = (arg0 );
        require(arg0  > 0xffffffffffffffff);
        require(0 < (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe0 + (0x20 + (arg0  << 0x05))));
        require(((var_c + 0xa0) < var_c) | ((var_c + 0xa0) > 0xffffffffffffffff));
        require(0 < (arg0 ));
        require(msg.data[(arg0 + 0) + 0x24] - (uint32(msg.data[(arg0 + 0) + 0x24])));
        require(((var_c + 0xa0) < var_c) | ((var_c + 0xa0) > 0xffffffffffffffff), "Oracle read failed");
        var_c = var_c + 0xa0;
        require(((var_c + 0x40) > 0xffffffffffffffff) | ((var_c + 0x40) < var_c), "Oracle read failed");
        var_c = var_c + 0x40;
        (bool success, bytes memory ret0) = address(0x0807).Unresolved_00000000(var_l); // staticcall
        require(!ret0.length, "Oracle read failed");
        require(((0x60 + var_q) - 0x60) < 0x20);
        require(var_d - (uint64(var_d)));
        require(!(uint64(var_d)), "Oracle price is zero");
        require(!(!var_q < 0x20), "Oracle read failed");
        require(ret0.length > 0xffffffffffffffff, "Oracle read failed");
        require(((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), "Oracle read failed");
        var_c = var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f));
        return abi.encodePacked(0x20, var_c.length);
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
    
    /// @custom:selector    0xc0182669
    /// @custom:signature   Unresolved_c0182669(uint32 arg0) public payable
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_c0182669(uint32 arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        var_b = 0x20;
        require(((var_c + 0x40) > 0xffffffffffffffff) | ((var_c + 0x40) < var_c), "BBO read failed");
        uint256 var_c = var_c + 0x40;
        (bool success, bytes memory ret0) = address(0x080e).Unresolved_00000000(var_f); // staticcall
        require(!ret0.length, "BBO read failed");
        require(((0x60 + var_k) - 0x60) < 0x40);
        require(var_b - (uint64(var_b)));
        require(!(!var_k < 0x40), "BBO read failed");
        require(ret0.length > 0xffffffffffffffff, "BBO read failed");
        require(((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), "BBO read failed");
    }
    
    /// @custom:selector    0xfb466481
    /// @custom:signature   Unresolved_fb466481(uint32 arg0) public payable
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_fb466481(uint32 arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        var_b = 0x20;
        require(((var_c + 0x40) > 0xffffffffffffffff) | ((var_c + 0x40) < var_c), "BBO read failed");
        uint256 var_c = var_c + 0x40;
        (bool success, bytes memory ret0) = address(0x080e).Unresolved_00000000(var_f); // staticcall
        require(!ret0.length, "BBO read failed");
        require(((0x60 + var_k) - 0x60) < 0x40);
        require(var_b - (uint64(var_b)));
        require(!(!var_k < 0x40), "BBO read failed");
        require(ret0.length > 0xffffffffffffffff, "BBO read failed");
        require(((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), "BBO read failed");
    }
}