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
    uint256 public constant unresolved_4f8632ba = 1436275596337742491148292629605903846977595690234;
    uint256 public constant unresolved_d2f7265a = 621329955008895694125364835068175551477650542754;
    
    error CustomError_00000000();
    event Event_3d95e1dd();
    
    /// @custom:selector    0x0c506e96
    /// @custom:signature   Unresolved_0c506e96(address arg0, uint256 arg1) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_0c506e96(address arg0, uint256 arg1) public payable {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(msg.sender - 0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa, "transfer failed");
        require(!arg1, "transfer failed");
        var_b = 0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa;
        var_d = 0x44;
        require(((var_e + 0x80) > 0xffffffffffffffff) | ((var_e + 0x80) < var_e), "transfer failed");
        uint256 var_e = var_e + 0x80;
        (bool success, bytes memory ret0) = address(arg0).Unresolved_a9059cbb(var_b); // call
        require(!ret0.length, "transfer failed");
        emit Event_3d95e1dd(0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa, address(arg0), arg1);
        require(var_l);
        require(((0x60 + var_l) - 0x60) < 0x20);
        require(var_d - var_d);
        require(ret0.length > 0xffffffffffffffff, "transfer failed");
        require(((var_e + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_e) | ((var_e + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), "transfer failed");
        var_e = var_e + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f));
        require(var_e.length, "transfer failed");
        require(var_e.length, "transfer failed");
        emit Event_3d95e1dd(0xfb94d3404c1d3d9d6f08f79e58041d5ea95accfa, address(arg0), arg1);
    }
    
    /// @custom:selector    0x925b3aad
    /// @custom:signature   Unresolved_925b3aad(uint64 arg0, uint64 arg1, uint64 arg2) public payable returns (uint256)
    /// @param              arg0 ["uint64", "bytes8", "int64"]
    /// @param              arg1 ["uint64", "bytes8", "int64"]
    /// @param              arg2 ["uint64", "bytes8", "int64"]
    function Unresolved_925b3aad(uint64 arg0, uint64 arg1, uint64 arg2) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (uint64(arg0)));
        require(arg1 - (uint64(arg1)));
        require(arg2 - (uint64(arg2)));
        require(msg.sender - 0x6cd5661646289fb6e65ea5c032310fded797d0a2, CustomError_fadaa871());
        require(!((!uint64(arg2)) | (0x64 == ((uint64(arg2) * 0x64) / (uint64(arg2))))), CustomError_fadaa871());
        require(uint64(arg1) > (uint64(arg1) + (uint64(arg2) * 0x64)), CustomError_fadaa871());
        require(uint64(arg1) + (uint64(arg2) * 0x64) > 0xffffffffffffffff, CustomError_fadaa871());
        require(uint64(arg2));
        require(((var_f + 0x60) > 0xffffffffffffffff) | ((var_f + 0x60) < var_f));
        uint256 var_f = var_f + 0x60;
        require((var_f + 0x60) + (uint248((((var_f + var_f.length) - var_f) + 0x24) + 0x1f)) < (var_f + 0x60) | ((var_f + 0x60) + (uint248((((var_f + var_f.length) - var_f) + 0x24) + 0x1f)) > 0xffffffffffffffff));
        var_f = (var_f + 0x60) + (uint248((((var_f + var_f.length) - var_f) + 0x24) + 0x1f));
        require(!address(0x3333333333333333333333333333333333333333).code.length);
        var_l = 0x20;
        require(0 < (var_n));
        (bool success, bytes memory ret0) = address(0x3333333333333333333333333333333333333333).Unresolved_17938e13(var_l); // call
        require(uint64(arg1) + (uint64(arg2) * 0x64), "only exchange");
        require(((var_f + 0x80) > 0xffffffffffffffff) | ((var_f + 0x80) < var_f), "only exchange");
        return ;
        require(var_f > 0xffffffffffffffff, "only exchange");
    }
}