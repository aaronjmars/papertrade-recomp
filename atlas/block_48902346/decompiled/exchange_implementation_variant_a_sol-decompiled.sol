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
    uint256 public constant unresolved_ff3bc415 = 64;
    uint256 public constant unresolved_af210ecc = 25;
    uint256 public constant unresolved_fdfd905d = 1000000000000000000;
    uint256 public constant unresolved_6d60ae8e = 1000000000;
    
    address public unresolved_21f55a6c;
    uint256 public unresolved_899346c7;
    mapping(bytes32 => bytes32) storage_map_ah;
    bytes32 unresolved_8da5cb5bb;
    mapping(bytes32 => bytes32) storage_map_aj;
    mapping(bytes32 => bytes32) storage_map_c;
    bool public unresolved_c43fbc8c;
    mapping(bytes32 => bytes32) storage_map_ac;
    address public unresolved_e1f9209b;
    address public unresolved_13dd495b;
    uint256 public unresolved_ec0bdcfc;
    uint256 public unresolved_48ee5e08;
    address public unresolved_9274682e;
    address public unresolved_7dc0d1d0;
    address public unresolved_c10f1a75;
    mapping(bytes32 => bytes32) storage_map_t;
    address public unresolved_9d47d4d3;
    uint256 public unresolved_96523644;
    address public unresolved_ed410ee1;
    uint256 public unresolved_61d027b3;
    uint256 public unresolved_53ac4b66;
    mapping(bytes32 => bytes32) storage_map_h;
    mapping(bytes32 => bytes32) storage_map_af;
    address public unresolved_cbeb5f3d;
    mapping(bytes32 => bytes32) storage_map_f;
    address public unresolved_a69a2ad1;
    address public unresolved_24a3d622;
    mapping(bytes32 => bytes32) storage_map_ag;
    mapping(bytes32 => bytes32) storage_map_g;
    uint256 public unresolved_5fb3b1b5;
    address public unresolved_8da5cb5b;
    bytes public unresolved_1b7c1009;
    uint32 public unresolved_f28bbdb2;
    bool public unresolved_53e23e2e;
    uint256 public unresolved_31a39849;
    uint256 public unresolved_f1a8786c;
    address public unresolved_afdf6702;
    mapping(bytes32 => bytes32) storage_map_ad;
    
    event Event_af809937();
    event Event_88451ea1();
    event Event_76a31977();
    event Event_06fb15b3();
    event Event_4ffd725f();
    event Event_6b3ffd50();
    event Event_c76a9da2();
    event Event_5bcf15b0();
    error CustomError_00000000();
    event Event_bcd09d92();
    event Event_8163d4e6();
    event Event_e7fd56ed();
    event Event_62db1b2b();
    event Event_4d57218e();
    event Event_3cfda8ee();
    event Event_e4af0531();
    event Event_abf32d7c();
    event Event_a065d6ba();
    event Event_25e933a2();
    event Event_7de91f01();
    event Event_18d8b795();
    event Event_a4abec92();
    
    /// @custom:selector    0x837fa3fd
    /// @custom:signature   Unresolved_837fa3fd(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_837fa3fd(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_53e23e2e = (address(arg0 << 0x08)) | (uint96(unresolved_53e23e2e));
        emit Event_4d57218e(address(arg0));
        return ;
    }
    
    /// @custom:selector    0x3a21be03
    /// @custom:signature   Unresolved_3a21be03(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_3a21be03(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_c[var_a];
    }
    
    /// @custom:selector    0x5ca4c0ea
    /// @custom:signature   Unresolved_5ca4c0ea(uint32 arg0, address arg1, uint96 arg2, uint96 arg3, uint64 arg4) public payable returns (uint256)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    /// @param              arg1 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg2 ["uint96", "bytes12", "int96"]
    /// @param              arg3 ["uint96", "bytes12", "int96"]
    /// @param              arg4 ["uint64", "bytes8", "int64"]
    function Unresolved_5ca4c0ea(uint32 arg0, address arg1, uint96 arg2, uint96 arg3, uint64 arg4) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg0 - (uint32(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (uint96(arg2)));
        require(arg3 - (uint96(arg3)));
        require(arg4 - (uint64(arg4)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        require(!(uint32(arg0) < (uint32(unresolved_f28bbdb2))), CustomError_b0cb274d());
        require(!(!address(arg1)), CustomError_b0cb274d());
        require(!(!uint96(arg3)), CustomError_b0cb274d());
        require(!(uint64(arg4) < 0x0de0b6b3a7640000), CustomError_b0cb274d());
        uint32 var_b = uint32(arg0);
        storage_map_f[var_b] = (address(storage_map_f[var_b])) | (address(arg1));
        storage_map_g[var_b] = (uint96(arg2 << 0x60)) | (address(storage_map_g[var_b]));
        storage_map_g[var_b] = (address(storage_map_g[var_b])) | (uint96(arg3));
        storage_map_h[var_b] = (uint64(arg4 << 0xb8)) | (uint192(storage_map_h[var_b]));
        emit Event_76a31977(uint32(arg0), address(arg1), uint96(arg2), uint96(arg3), uint64(arg4));
        return ;
        require(!(uint96(arg3)), CustomError_b0cb274d());
        var_b = uint32(arg0);
        storage_map_f[var_b] = (address(storage_map_f[var_b])) | (address(arg1));
        storage_map_g[var_b] = (uint96(arg2 << 0x60)) | (address(storage_map_g[var_b]));
        storage_map_g[var_b] = (address(storage_map_g[var_b])) | (uint96(arg3));
        storage_map_h[var_b] = (uint64(arg4 << 0xb8)) | (uint192(storage_map_h[var_b]));
        emit Event_76a31977(uint32(arg0), address(arg1), uint96(arg2), uint96(arg3), uint64(arg4));
        return ;
    }
    
    /// @custom:selector    0xe538b280
    /// @custom:signature   Unresolved_e538b280(uint256 arg0, uint256 arg1, uint256 arg2) public payable returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_e538b280(uint256 arg0, uint256 arg1, uint256 arg2) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60, CustomError_30cd7471());
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        require(!(arg0 > 0x06f05b59d3b20000), CustomError_cd4e6167());
        require(!(arg0 > 0x06f05b59d3b20000), CustomError_cd4e6167());
        require(arg0 > 0x06f05b59d3b20000, CustomError_cd4e6167());
        unresolved_f1a8786c = arg0;
        unresolved_48ee5e08 = arg1;
        unresolved_5fb3b1b5 = arg2;
        emit Event_e4af0531(arg0, arg1, arg2);
        return ;
    }
    
    /// @custom:selector    0xb3060d36
    /// @custom:signature   Unresolved_b3060d36(uint256 arg0) public view returns (address)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_b3060d36(uint256 arg0) public view returns (address) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        return address(storage_map_c[var_a]);
    }
    
    /// @custom:selector    0xf728fc98
    /// @custom:signature   Unresolved_f728fc98(uint256 arg0) public view returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_f728fc98(uint256 arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        return storage_map_c[var_a];
    }
    
    /// @custom:selector    0x70f75ff5
    /// @custom:signature   Unresolved_70f75ff5(uint256 arg0) public view returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_70f75ff5(uint256 arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(!(((arg0 * unresolved_31a39849) / arg0) == unresolved_31a39849) | !arg0);
        return arg0 * unresolved_31a39849;
    }
    
    /// @custom:selector    0x2d2451d1
    /// @custom:signature   Unresolved_2d2451d1(uint32 arg0) public payable returns (uint256)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_2d2451d1(uint32 arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        require(!(msg.sender == (address(unresolved_8da5cb5b >> 0x10))), CustomError_49199fb6());
        require(!(msg.sender == (address(unresolved_24a3d622))), CustomError_49199fb6());
        require(!(uint32(arg0) < (uint32(unresolved_f28bbdb2))), CustomError_0d240815());
        uint32 var_b = uint32(arg0);
        require(bytes1(storage_map_g[var_b]), CustomError_0d240815());
        var_b = uint32(arg0);
        uint32 var_d = uint32(storage_map_g[var_b] >> 0xc0);
        (bool success, bytes memory ret0) = address(unresolved_7dc0d1d0).Unresolved_fb466481(var_d); // staticcall
        storage_map_g[var_b] = 0x01 | (uint64(block.timestamp << 0x88) | ((uint56(storage_map_g[var_b]) | 0) | 0));
        emit Event_25e933a2(uint32(arg0), 0, 0, uint64(block.timestamp));
        return ;
        require(0x40 > ret0.length);
        require(((var_g + 0x40) < var_g) | ((var_g + 0x40) > 0xffffffffffffffff));
        uint256 var_g = var_g + 0x40;
        require(((var_g + 0x40) - var_g) < 0x40);
        require(var_g.length - (uint64(var_g.length)));
    }
    
    /// @custom:selector    0x48bde20c
    /// @custom:signature   Unresolved_48bde20c(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_48bde20c(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_24a3d622 = (address(arg0)) | (uint96(unresolved_24a3d622));
        emit Event_6b3ffd50(address(arg0));
        return ;
    }
    
    /// @custom:selector    0xae69b95b
    /// @custom:signature   Unresolved_ae69b95b(uint256 arg0) public payable returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_ae69b95b(uint256 arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - arg0);
        require(!(msg.sender == (address(unresolved_8da5cb5b >> 0x10))), CustomError_49199fb6());
        require(msg.sender == (address(unresolved_24a3d622)), CustomError_49199fb6());
        require(!(msg.sender == (address(unresolved_24a3d622))), CustomError_49199fb6());
        unresolved_53e23e2e = (bytes1(arg0)) | (uint248(unresolved_53e23e2e));
        emit Event_a4abec92(arg0);
        return ;
        require(!arg0, CustomError_49199fb6());
        unresolved_53e23e2e = (bytes1(arg0)) | (uint248(unresolved_53e23e2e));
        emit Event_a4abec92(arg0);
        return ;
    }
    
    /// @custom:selector    0xcd2d3811
    /// @custom:signature   Unresolved_cd2d3811(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_cd2d3811(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        require(!(!address(unresolved_e1f9209b)), CustomError_612a3522());
        require(!(address(arg0) == (address(unresolved_e1f9209b))), CustomError_612a3522());
        unresolved_e1f9209b = (address(arg0)) | (uint96(unresolved_e1f9209b));
        emit Event_bcd09d92(address(arg0));
        return ;
    }
    
    /// @custom:selector    0x32faa570
    /// @custom:signature   Unresolved_32faa570(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_32faa570(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_c[var_a];
    }
    
    /// @custom:selector    0x7b9f5264
    /// @custom:signature   Unresolved_7b9f5264() public payable returns (uint256)
    function Unresolved_7b9f5264() public payable returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0);
        require(!address(unresolved_e1f9209b));
        require(!address(unresolved_afdf6702));
        unresolved_afdf6702 = address(unresolved_afdf6702);
        require(unresolved_53ac4b66);
        require(!0 < (address(unresolved_afdf6702)));
        require(0);
        address var_a = address(unresolved_e1f9209b);
        require(storage_map_c[var_a] > (storage_map_c[var_a] + 0));
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        storage_map_c[var_a] = storage_map_c[var_a] + 0;
        require((address(unresolved_a69a2ad1) + 0) > 0xffffffffffffffffffffffffffffffff);
        unresolved_a69a2ad1 = (address(unresolved_a69a2ad1 + 0)) | (address(unresolved_a69a2ad1));
        require(0 < (address(unresolved_afdf6702)));
        require(!address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).code.length);
        var_e = 0x0f;
        address var_f = address(unresolved_e1f9209b);
        (bool success, bytes memory ret0) = address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).Unresolved_18958ce2(var_e); // delegatecall
        emit Event_18d8b795(address(unresolved_e1f9209b), address(unresolved_afdf6702), 0);
        require(!address(unresolved_ed410ee1));
        (bool success, bytes memory ret0) = address(unresolved_ed410ee1).Unresolved_ae745703(var_e); // staticcall
        require(!0);
        require(!address(unresolved_ed410ee1).code.length);
        uint256 var_e = 0;
        (bool success, bytes memory ret0) = address(unresolved_ed410ee1).Unresolved_c218c676(var_e, var_f); // call
        require(var_i > 0xffffffffffffffff);
        return ;
        require(0x20 > ret0.length);
        require(((var_i + 0x20) < var_i) | ((var_i + 0x20) > 0xffffffffffffffff));
        uint256 var_i = var_i + 0x20;
        require(((var_i + 0x20) - var_i) < 0x20);
        require(!var_i.length);
        return ;
        require(!address(unresolved_ed410ee1).code.length);
        var_f = var_i.length;
        (bool success, bytes memory ret0) = address(unresolved_ed410ee1).Unresolved_c218c676(var_f); // call
        require(var_i > 0xffffffffffffffff, CustomError_64cd1788());
    }
    
    /// @custom:selector    0x6d142da1
    /// @custom:signature   Unresolved_6d142da1(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_6d142da1(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(!address(unresolved_c10f1a75));
        address var_b = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_c10f1a75).Unresolved_c1a9a508(var_b); // staticcall
        require(!0, CustomError_d26ffacb());
        address var_c = address(arg0);
        require(!storage_map_t[var_c], CustomError_d26ffacb());
        require(!(block.number > (uint32(storage_map_t[var_c] >> 0x80))), CustomError_d26ffacb());
        var_a = 0x40;
        require(((var_g + 0x60) < var_g) | ((var_g + 0x60) > 0xffffffffffffffff), CustomError_0a9e0180());
        uint256 var_g = var_g + 0x60;
        (bool success, bytes memory ret0) = address(0x0801).Unresolved_00000000(var_i, var_j); // staticcall
        require(!ret0.length, CustomError_0a9e0180());
        require(((0x60 + var_l) - 0x60) < 0x60);
        require(var_a - (uint64(var_a)));
        require(var_l < 0x60, CustomError_0a9e0180());
        require(ret0.length > 0xffffffffffffffff, CustomError_0a9e0180());
        require(((var_g + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_g) | ((var_g + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), CustomError_0a9e0180());
        if (0x20 > ret0.length) {
        }
    }
    
    /// @custom:selector    0xfb9f1009
    /// @custom:signature   Unresolved_fb9f1009(uint32 arg0) public pure
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_fb9f1009(uint32 arg0) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
    }
    
    /// @custom:selector    0x599dc539
    /// @custom:signature   Unresolved_599dc539(uint256 arg0) public view
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_599dc539(uint256 arg0) public view {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 > 0xffffffffffffffff);
        require(arg0 > 0xffffffffffffffff);
        require(uint32(unresolved_f28bbdb2) > 0xffffffffffffffff);
        require(((var_c + (uint248((0x20 + (uint32(unresolved_f28bbdb2) << 0x05)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (uint32(unresolved_f28bbdb2) << 0x05)) + 0x1f))) > 0xffffffffffffffff));
        require(uint32(unresolved_f28bbdb2) > 0xffffffffffffffff);
    }
    
    /// @custom:selector    0xc88bbcf3
    /// @custom:signature   Unresolved_c88bbcf3(uint96 arg0, uint96 arg1, uint32 arg2, uint32 arg3, address arg4, uint64 arg5, uint64 arg6, address arg7, uint64 arg8) public payable
    /// @param              arg0 ["uint96", "bytes12", "int96"]
    /// @param              arg1 ["uint96", "bytes12", "int96"]
    /// @param              arg2 ["uint32", "bytes4", "int32"]
    /// @param              arg3 ["uint32", "bytes4", "int32"]
    /// @param              arg4 ["address", "uint120", "bytes15", "int120"]
    /// @param              arg5 ["uint64", "bytes8", "int64"]
    /// @param              arg6 ["uint64", "bytes8", "int64"]
    /// @param              arg7 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg8 ["uint64", "bytes8", "int64"]
    function Unresolved_c88bbcf3(uint96 arg0, uint96 arg1, uint32 arg2, uint32 arg3, address arg4, uint64 arg5, uint64 arg6, address arg7, uint64 arg8) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x0120);
        require(0x0100 > (0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length));
        require(arg8 - (uint64(arg8)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        require(arg3 - (uint32(arg3)));
        require(!uint32(arg3));
        require(arg5 - (uint64(arg5)));
        require(!(uint64(arg5) < 0x0de0b6b3a7640000), CustomError_b0cb274d());
        require(arg6 - (uint64(arg6)));
        require(!(uint64(arg6) < 0x0de0b6b3a7640000), CustomError_b0cb274d());
        require(arg0 - (uint96(arg0)));
        require(!uint96(arg0));
        require(arg7 - (address(arg7)));
        require(!address(arg7));
        require(arg4 - (address(arg4)));
        require(!address(arg4));
        require(!uint64(arg8));
        require(uint32(unresolved_f28bbdb2) == 0xffffffff);
        unresolved_f28bbdb2 = (uint32(unresolved_f28bbdb2 + 0x01)) | (uint224(unresolved_f28bbdb2));
        uint32 var_b = uint32(unresolved_f28bbdb2);
        require(arg0 - (uint96(arg0)));
        storage_map_g[var_b] = (uint96(arg0)) | (address(storage_map_g[var_b]));
        require(arg1 - (uint96(arg1)));
        storage_map_g[var_b] = (uint96(arg1 << 0x60)) | (address(storage_map_g[var_b]));
        require(arg2 - (uint32(arg2)));
        storage_map_g[var_b] = (uint32(arg2 << 0xc0)) | (uint224(storage_map_g[var_b]));
        require(arg3 - (uint32(arg3)));
        storage_map_g[var_b] = (uint32(arg3 << 0xe0)) | (uint224(storage_map_g[var_b]));
        require(arg4 - (address(arg4)));
        require(arg5 - (uint64(arg5)));
        storage_map_h[var_b] = (uint72(storage_map_h[var_b]) | (address(arg4))) | (uint64(arg5 << 0x78));
        require(arg6 - (uint64(arg6)));
        storage_map_h[var_b] = (uint64(arg6 << 0xb8)) | (uint192(storage_map_h[var_b]));
        require(arg7 - (address(arg7)));
    }
    
    /// @custom:selector    0x86d506db
    /// @custom:signature   Unresolved_86d506db(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_86d506db(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_cbeb5f3d = (address(arg0)) | (uint96(unresolved_cbeb5f3d));
        emit Event_7de91f01(address(arg0));
        return ;
    }
    
    /// @custom:selector    0x2dcc7fce
    /// @custom:signature   Unresolved_2dcc7fce(uint256 arg0) public view returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_2dcc7fce(uint256 arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(!(((arg0 * unresolved_ec0bdcfc) / arg0) == unresolved_ec0bdcfc) | !arg0);
        require(!unresolved_31a39849);
        return (arg0 * unresolved_ec0bdcfc) / unresolved_31a39849;
    }
    
    /// @custom:selector    0x827ad94c
    /// @custom:signature   Unresolved_827ad94c(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_827ad94c(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x80);
        require(arg0 - (address(arg0)));
        var_b = 0x0f;
        (bool success, bytes memory ret0) = address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).Unresolved_32db40c9(var_b); // delegatecall
        return abi.encodePacked(0, 0, 0);
        require(0x60 > ret0.length);
        require(((var_i + 0x60) < var_i) | ((var_i + 0x60) > 0xffffffffffffffff));
        uint256 var_i = var_i + 0x60;
        require(((var_i + 0x60) - var_i) < 0x60);
        return abi.encodePacked(var_i.length, var_q, var_r);
    }
    
    /// @custom:selector    0x060447aa
    /// @custom:signature   Unresolved_060447aa(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_060447aa(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_21f55a6c = (address(arg0)) | (uint96(unresolved_21f55a6c));
        emit Event_c76a9da2(address(arg0));
    }
    
    /// @custom:selector    0xdcab7f6a
    /// @custom:signature   Unresolved_dcab7f6a(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_dcab7f6a(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_c[var_a];
    }
    
    /// @custom:selector    0x18715c9a
    /// @custom:signature   Unresolved_18715c9a() public payable returns (uint256)
    function Unresolved_18715c9a() public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0);
        require(!address(unresolved_ed410ee1));
        (bool success, bytes memory ret0) = address(unresolved_ed410ee1).Unresolved_ae745703(var_b); // staticcall
        return 0;
        require(0x20 > ret0.length);
        require(((var_c + 0x20) < var_c) | ((var_c + 0x20) > 0xffffffffffffffff));
        uint256 var_c = var_c + 0x20;
        require(((var_c + 0x20) - var_c) < 0x20);
        return var_c.length;
        return 0;
    }
    
    /// @custom:selector    0x7f99545a
    /// @custom:signature   Unresolved_7f99545a(uint256 arg0) public view
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_7f99545a(uint256 arg0) public view {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20, CustomError_4f57ffae());
        address var_a = address(msg.sender);
        require(!(block.number > storage_map_c[var_a]), CustomError_4f57ffae());
        require(!(((arg0 * unresolved_ec0bdcfc) / arg0) == unresolved_ec0bdcfc) | !arg0);
    }
    
    /// @custom:selector    0x82f47a3f
    /// @custom:signature   Unresolved_82f47a3f(address arg0, address arg1) public payable returns (uint256)
    /// @param              arg0 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg1 ["address", "uint128", "bytes16", "int128"]
    function Unresolved_82f47a3f(address arg0, address arg1) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(!(msg.sender == (address(unresolved_8da5cb5b >> 0x10))), CustomError_989c4c7c());
        require(!(msg.sender == (address(unresolved_21f55a6c))), CustomError_989c4c7c());
        require(((var_b + 0x40) < var_b) | ((var_b + 0x40) > 0xffffffffffffffff));
        unresolved_1b7c1009 = (address(arg1 << 0x80)) | (address(arg0));
        emit Event_5bcf15b0(address(arg0), address(arg1));
        return ;
    }
    
    /// @custom:selector    0xc0c53b8b
    /// @custom:signature   Unresolved_c0c53b8b(address arg0, address arg1, address arg2) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_c0c53b8b(address arg0, address arg1, address arg2) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
        require(bytes1(unresolved_8da5cb5b), CustomError_6a426315());
        require(!(bytes1(unresolved_8da5cb5b >> 0x08)), CustomError_6a426315());
        require(!(bytes1(unresolved_8da5cb5b >> 0x08)), CustomError_6a426315());
        unresolved_8da5cb5b = (address(arg0 << 0x10)) | (uint96(unresolved_8da5cb5b));
        unresolved_24a3d622 = (address(arg0)) | (uint96(unresolved_24a3d622));
        unresolved_7dc0d1d0 = (address(arg1)) | (uint96(unresolved_7dc0d1d0));
        unresolved_f1a8786c = 0x470de4df820000;
        unresolved_48ee5e08 = 0x470de4df820000;
        unresolved_5fb3b1b5 = 0x470de4df820000;
        unresolved_1b7c1009 = 0x0de0b6b3a7640000 | (address(unresolved_1b7c1009));
        (bool success, bytes memory ret0) = address(arg2).Unresolved_313ce567(var_b); // staticcall
        require(0x06 > 0x12, CustomError_6a426315());
        unresolved_ec0bdcfc = 0xe8d4a51000;
        require(0x10 < 0x06);
        unresolved_8da5cb5ba = (uint248(unresolved_8da5cb5ba)) | 0x06;
        unresolved_31a39849 = 0xe8d4a51000;
        unresolved_8da5cb5bb = 0x01;
        emit Event_4ffd725f(address(arg0));
        require(!bytes1(unresolved_8da5cb5b >> 0x08));
        return ;
        unresolved_8da5cb5b = (uint88(unresolved_8da5cb5b)) | (address(arg0 << 0x10));
        return ;
        require(0x20 > ret0.length);
        require(((var_d + 0x20) < var_d) | ((var_d + 0x20) > 0xffffffffffffffff));
        uint256 var_d = var_d + 0x20;
        require(((var_d + 0x20) - var_d) < 0x20);
        require(var_d.length - (bytes1(var_d.length)));
        unresolved_8da5cb5b = 0x0101 | (uint240(unresolved_8da5cb5b));
        unresolved_8da5cb5b = (address(arg0 << 0x10)) | (uint96(unresolved_8da5cb5b));
        unresolved_24a3d622 = (address(arg0)) | (uint96(unresolved_24a3d622));
        unresolved_7dc0d1d0 = (address(arg1)) | (uint96(unresolved_7dc0d1d0));
        unresolved_f1a8786c = 0x470de4df820000;
        unresolved_48ee5e08 = 0x470de4df820000;
        unresolved_5fb3b1b5 = 0x470de4df820000;
        unresolved_1b7c1009 = 0x0de0b6b3a7640000 | (address(unresolved_1b7c1009));
        (bool success, bytes memory ret0) = address(arg2).Unresolved_313ce567(var_b); // staticcall
        if (0x20 > ret0.length) {
        }
        require(bytes1(unresolved_8da5cb5b), CustomError_0dc149f0());
    }
    
    /// @custom:selector    0xfbddd751
    /// @custom:signature   Unresolved_fbddd751(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_fbddd751(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_c10f1a75 = (address(arg0)) | (uint96(unresolved_c10f1a75));
        emit Event_06fb15b3(address(arg0));
        return ;
    }
    
    /// @custom:selector    0xddc63262
    /// @custom:signature   Unresolved_ddc63262(uint256 arg0) public view
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_ddc63262(uint256 arg0) public view {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20, CustomError_75e52f4f());
        require(!unresolved_53ac4b66, CustomError_75e52f4f());
        require(address(unresolved_a69a2ad1) > (address(unresolved_a69a2ad1) + (unresolved_a69a2ad1 >> 0x80)), CustomError_75e52f4f());
    }
    
    /// @custom:selector    0xcb163b03
    /// @custom:signature   Unresolved_cb163b03(uint32 arg0) public view returns (bytes memory)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_cb163b03(uint32 arg0) public view returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        uint32 var_a = uint32(arg0);
        return abi.encodePacked(uint96(storage_map_c[var_a]), uint96(storage_map_c[var_a] >> 0x60), address(storage_map_ac[var_a]), (storage_map_ac[var_a]) >> 0x80, storage_map_c[var_a] >> 0xc0);
    }
    
    /// @custom:selector    0xdc8a47ef
    /// @custom:signature   Unresolved_dc8a47ef(uint32 arg0) public view returns (bytes memory)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_dc8a47ef(uint32 arg0) public view returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        uint32 var_a = uint32(arg0);
        return abi.encodePacked(uint96(storage_map_c[var_a]), uint96(storage_map_c[var_a] >> 0x60), uint32(storage_map_c[var_a] >> 0xc0), storage_map_c[var_a] >> 0xe0, address(storage_map_ac[var_a]), uint64(storage_map_ac[var_a] >> 0x78), uint64(storage_map_ac[var_a] >> 0xb8), address(storage_map_ad[var_a]));
    }
    
    /// @custom:selector    0x551306f3
    /// @custom:signature   Unresolved_551306f3(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_551306f3(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_c[var_a];
    }
    
    /// @custom:selector    0xec6783f0
    /// @custom:signature   Unresolved_ec6783f0(address arg0, uint32 arg1, uint256 arg2, address arg3, uint32 arg4, uint256 arg5, uint256 arg6, uint64 arg7, bool arg8, uint256 arg9, uint256 arg10) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint32", "bytes4", "int32"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg4 ["uint32", "bytes4", "int32"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    /// @param              arg6 ["uint256", "bytes32", "int256"]
    /// @param              arg7 ["uint64", "bytes8", "int64"]
    /// @param              arg8 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg9 ["uint256", "bytes32", "int256"]
    /// @param              arg10 ["uint256", "bytes32", "int256"]
    function Unresolved_ec6783f0(address arg0, uint32 arg1, uint256 arg2, address arg3, uint32 arg4, uint256 arg5, uint256 arg6, uint64 arg7, bool arg8, uint256 arg9, uint256 arg10) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x0160);
        require(arg0 - (address(arg0)));
        require(arg1 - (uint32(arg1)));
        require(arg2 - arg2);
        require(arg3 - (address(arg3)));
        require(arg4 - (uint32(arg4)));
        require(arg5 - arg5);
        require(arg7 - (uint64(arg7)));
        require(arg8 - (bytes1(arg8)));
        require(msg.sender - (address(unresolved_8da5cb5be)), CustomError_da96f0b6());
        require(!address(unresolved_53e23e2e >> 0x08).code.length);
        address var_b = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_53e23e2e >> 0x08).Unresolved_b002b9fa(var_b); // call
        require((0xffffffffffffffff < (var_n + 0x0140)) | (var_n > (var_n + 0x0140)));
        address var_r = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_53e23e2e >> 0x08).Unresolved_7f608253(var_r); // staticcall
        require(bytes1(unresolved_53e23e2e), CustomError_02b874a6());
        require(!(uint32(arg1) < (uint32(unresolved_f28bbdb2))), CustomError_741df939());
        uint32 var_o = uint32(arg1);
        require(bytes1(storage_map_af[var_o]), CustomError_741df939());
        require(!(uint32(arg4)), CustomError_0a4f5a07());
        require(uint32(arg4) > (storage_map_af[var_o] >> 0xe0), CustomError_0a4f5a07());
        require(address(arg3) < (address(unresolved_1b7c1009)), CustomError_25a1ddf3());
        require(!(address(arg3) * (uint32(arg4)) / (address(arg3)) == (uint32(arg4)) | (!address(arg3))), CustomError_9f65ace4());
        var_o = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(address(arg3) * (uint32(arg4)) < (unresolved_1b7c1009 >> 0x80), CustomError_9f65ace4());
        require(address(arg3) * (uint32(arg4)) > (address(storage_map_ag[var_o])), CustomError_543a6e10());
        var_o = uint32(arg1);
        require(bytes1(storage_map_af[var_o]), CustomError_1b7f36f3());
        require(uint64(storage_map_af[var_o] >> 0x08) > (uint64(storage_map_af[var_o] >> 0x08) + (uint64(storage_map_af[var_o] >> 0x48))), CustomError_1b7f36f3());
        var_o = uint32(arg1);
        require(!(uint64(storage_map_af[var_o] >> 0xc0)), CustomError_1b7f36f3());
        require(!(address(arg3) * (uint32(arg4)) * (uint64(storage_map_af[var_o] >> 0xc0)) / (address(arg3) * (uint32(arg4))) == (uint64(storage_map_af[var_o] >> 0xc0)) | (!(address(arg3)) * (uint32(arg4)))), CustomError_1b7f36f3());
        var_o = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(!(uint64((storage_map_af[var_o] >> 0x08) + (storage_map_af[var_o] >> 0x48) >> 0x01)), CustomError_1b7f36f3());
        require(address(arg3) * (uint32(arg4)) * (uint64(storage_map_af[var_o] >> 0xc0)) / (uint64((storage_map_af[var_o] >> 0x08) + (storage_map_af[var_o] >> 0x48) >> 0x01)) > 0xffffffffffffffffffffffff, CustomError_1b7f36f3());
        var_o = uint32(arg1);
        require(0 == arg2, CustomError_40f92143());
        require(uint96(storage_map_af[var_o]) + (uint96(address(arg3) * (uint32(arg4)) * (uint64(storage_map_af[var_o] >> 0xc0)) / (uint64(uint64(uint64(storage_map_af[var_o] >> 0x08) + (uint64(storage_map_af[var_o] >> 0x48)) >> 0x01))))) > 0xffffffffffffffffffffffff, CustomError_40f92143());
        var_o = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(uint96(storage_map_af[var_o] + (address(arg3) * (uint32(arg4)) * (uint64(storage_map_af[var_o] >> 0xc0)) / (uint64(uint64(uint64(storage_map_af[var_o] >> 0x08) + (uint64(storage_map_af[var_o] >> 0x48)) >> 0x01))))) > (address(storage_map_ah[var_o])), CustomError_40f92143());
        storage_map_af[var_o] = (address(storage_map_af[var_o])) | (uint96(storage_map_af[var_o] + (address(arg3) * (uint32(arg4)) * (uint64(storage_map_af[var_o] >> 0xc0)) / (uint64(uint64(uint64(storage_map_af[var_o] >> 0x08) + (uint64(storage_map_af[var_o] >> 0x48)) >> 0x01))))));
        require(!arg5, CustomError_8e667356());
        var_o = address(arg0);
        require(address(arg3) > storage_map_af[var_o], CustomError_8e667356());
        require(!address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).code.length);
        var_r = 0x0f;
        address var_s = address(arg0);
        (bool success, bytes memory ret0) = address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).Unresolved_3f4e3626(var_r); // delegatecall
        if (!unresolved_53ac4b66) {
            require(!unresolved_53ac4b66);
            unresolved_8da5cb5bi = unresolved_8da5cb5bi + 0x01;
            require(!unresolved_53ac4b66);
            var_o = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            var_n = var_n + 0x0120;
            var_o = unresolved_8da5cb5bi;
            storage_map_af[var_o] = (uint32(var_t << 0xa0)) | (address(var_n.length) | (uint64(storage_map_af[var_o])));
            storage_map_af[var_o] = (uint64(var_ag << 0xc0)) | (uint192(storage_map_af[var_o]));
            storage_map_ag[var_o] = (bytes1((var_ah) << 0xf0)) | (bytes1((var_ai) << 0xe8) | (bytes1((var_aj) << 0xe0) | (uint64(var_ak << 0xa0) | (uint32(var_al << 0x80) | (address(var_am) | (bytes1(storage_map_ag[var_o])))))));
            require(((var_n + 0x0120) > 0xffffffffffffffff) | ((var_n + 0x0120) < var_n));
            var_o = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            storage_map_af[var_o] = storage_map_af[var_o] + 0x01;
            require(!storage_map_af[var_o] < 0x010000000000000000);
            var_o = keccak256(var_o);
            storage_map_aj[var_o] = (0 & (storage_map_aj[var_o])) | (unresolved_8da5cb5bi << 0);
            var_o = unresolved_8da5cb5bi;
            storage_map_af[var_o] = storage_map_af[var_o];
            emit Event_88451ea1(unresolved_8da5cb5bi, address(arg0), uint32(arg1), arg2, arg5, uint64((storage_map_af[var_o] >> 0x08) + (storage_map_af[var_o] >> 0x48) >> 0x01), address(arg3), uint32(arg4));
            return unresolved_8da5cb5bi;
            require(!storage_map_af[var_o] < storage_map_af[var_o]);
        }
        require(var_n > 0xffffffffffffffff);
        var_n = var_n;
        require(0);
        var_o = address(arg0);
        require(storage_map_af[var_o] < (address(arg3)), CustomError_f4d678b8());
        var_o = address(arg0);
        storage_map_af[var_o] = storage_map_af[var_o] - (address(arg3));
        require(address((unresolved_a69a2ad1 - arg3) | (unresolved_a69a2ad1) >> 0x80) + (address(arg3)) > 0xffffffffffffffffffffffffffffffff, CustomError_924d25e6());
        var_o = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        var_r = uint32(storage_map_af[var_o] >> 0xc0);
        (bool success, bytes memory ret0) = address(unresolved_7dc0d1d0).Unresolved_c0182669(var_r, var_s); // staticcall
        require(0x20 > ret0.length);
        require(((var_n + 0x20) < var_n) | ((var_n + 0x20) > 0xffffffffffffffff));
        var_n = var_n + 0x20;
        require(((var_n + 0x20) - var_n) < 0x20);
        require(var_n.length - (uint64(var_n.length)), CustomError_924d25e6());
        var_o = uint32(arg1);
        require(!(uint64(storage_map_af[var_o] >> 0xc0)), CustomError_924d25e6());
        require(!(address(arg3) * (uint32(arg4)) * (uint64(storage_map_af[var_o] >> 0xc0)) / (address(arg3) * (uint32(arg4))) == (uint64(storage_map_af[var_o] >> 0xc0)) | (!(address(arg3)) * (uint32(arg4)))), CustomError_924d25e6());
        if (0x20 > ret0.length) {
        }
    }
    
    /// @custom:selector    0x0cdd5fc4
    /// @custom:signature   Unresolved_0cdd5fc4() public view returns (uint256)
    function Unresolved_0cdd5fc4() public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0);
        if (unresolved_53ac4b66) {
            return 0;
            if (address(unresolved_a69a2ad1) > (address(unresolved_a69a2ad1) + (unresolved_a69a2ad1 >> 0x80))) {
            }
        }
    }
    
    /// @custom:selector    0x4a4d9eea
    /// @custom:signature   Unresolved_4a4d9eea(address arg0, uint256 arg1, uint256 arg2) public payable returns (bytes memory)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_4a4d9eea(address arg0, uint256 arg1, uint256 arg2) public payable returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        var_b = 0x0f;
        (bool success, bytes memory ret0) = address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).Unresolved_ca02ff91(var_b); // delegatecall
        return abi.encodePacked(0, 0, 0);
        require(0x60 > ret0.length);
        require(((var_h + 0x60) < var_h) | ((var_h + 0x60) > 0xffffffffffffffff));
        uint256 var_h = var_h + 0x60;
        require(((var_h + 0x60) - var_h) < 0x60);
        return abi.encodePacked(var_h.length, var_p, var_q);
    }
    
    /// @custom:selector    0x2792e706
    /// @custom:signature   Unresolved_2792e706(address arg0, uint256 arg1, uint256 arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint64", "bytes8", "int64"]
    /// @param              arg4 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    /// @param              arg6 ["uint256", "bytes32", "int256"]
    function Unresolved_2792e706(address arg0, uint256 arg1, uint256 arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xe0);
        require(arg0 - (address(arg0)));
        require(arg1 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(arg3 - (uint64(arg3)));
        require(arg4 - (bytes1(arg4)));
        require(msg.sender - (address(unresolved_8da5cb5be)), CustomError_da96f0b6());
        require(!address(unresolved_53e23e2e >> 0x08).code.length);
        address var_b = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_53e23e2e >> 0x08).Unresolved_b002b9fa(var_b); // call
        require(arg1 > 0x07ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
        var_e = msg.data[36:36];
        require(((var_f + (uint248((((var_f + (arg1 << 0x05)) - var_f) + 0x20) + 0x1f))) < var_f) | ((var_f + (uint248((((var_f + (arg1 << 0x05)) - var_f) + 0x20) + 0x1f))) > 0xffffffffffffffff));
        uint256 var_f = var_f + (uint248((((var_f + (arg1 << 0x05)) - var_f) + 0x20) + 0x1f));
        require(((var_f + 0xc0) > 0xffffffffffffffff) | ((var_f + 0xc0) < var_f));
        var_f = var_f + 0xc0;
        address var_p = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_53e23e2e >> 0x08).Unresolved_7f608253(var_p); // staticcall
        require(!(arg1), CustomError_8431a15a());
        require(arg1 > 0x19, CustomError_8431a15a());
        require((var_f > (var_f + 0x0160)) | ((var_f + 0x0160) > 0xffffffffffffffff), CustomError_ad0ef2c5());
        var_f = var_f + 0x0160;
        require(unresolved_53ac4b66, CustomError_ad0ef2c5());
        require(uint32(unresolved_f28bbdb2) > 0xffffffffffffffff, CustomError_ad0ef2c5());
        require(((var_f + (uint248((0x20 + (uint32(unresolved_f28bbdb2) << 0x05)) + 0x1f))) < var_f) | ((var_f + (uint248((0x20 + (uint32(unresolved_f28bbdb2) << 0x05)) + 0x1f))) > 0xffffffffffffffff), CustomError_ad0ef2c5());
        var_f = var_f + (uint248((0x20 + (uint32(unresolved_f28bbdb2) << 0x05)) + 0x1f));
        require(uint32(unresolved_f28bbdb2) > 0xffffffffffffffff, CustomError_ad0ef2c5());
        require(address(unresolved_a69a2ad1) > (address(unresolved_a69a2ad1) + (unresolved_a69a2ad1 >> 0x80)), CustomError_ad0ef2c5());
        if (0x20 > ret0.length) {
        }
        require(var_f > 0xffffffffffffffff);
    }
    
    /// @custom:selector    0x58d3ec6a
    /// @custom:signature   Unresolved_58d3ec6a(uint256 arg0) public pure
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_58d3ec6a(uint256 arg0) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 > 0xffffffffffffffff);
        require(arg0 > 0xffffffffffffffff);
    }
    
    /// @custom:selector    0xbacd9ea0
    /// @custom:signature   Unresolved_bacd9ea0(uint256 arg0) public view returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_bacd9ea0(uint256 arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(!(((arg0 * unresolved_ec0bdcfc) / arg0) == unresolved_ec0bdcfc) | !arg0);
        return arg0 * unresolved_ec0bdcfc;
    }
    
    /// @custom:selector    0x27e235e3
    /// @custom:signature   Unresolved_27e235e3(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_27e235e3(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_c[var_a];
    }
    
    /// @custom:selector    0xe0189108
    /// @custom:signature   Unresolved_e0189108(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_e0189108(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(!address(unresolved_c10f1a75));
        address var_b = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_c10f1a75).Unresolved_c1a9a508(var_b); // staticcall
        require(!0, CustomError_28ef4314());
        address var_c = address(arg0);
        require(storage_map_t[var_c], CustomError_28ef4314());
        var_c = 0;
        require(!(block.number > storage_map_t[var_c]), CustomError_fefe83a0());
        var_c = 0;
        storage_map_t[var_c] = block.number;
        var_a = 0x40;
        require(((var_g + 0x60) < var_g) | ((var_g + 0x60) > 0xffffffffffffffff), CustomError_0a9e0180());
        uint256 var_g = var_g + 0x60;
        (bool success, bytes memory ret0) = address(0x0801).Unresolved_00000000(var_i, var_j); // staticcall
        require(!ret0.length, CustomError_0a9e0180());
        require(((0x60 + var_l) - 0x60) < 0x60);
        require(var_a - (uint64(var_a)));
        require(var_l < 0x60, CustomError_0a9e0180());
        require(ret0.length > 0xffffffffffffffff, CustomError_0a9e0180());
        require(((var_g + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_g) | ((var_g + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), CustomError_0a9e0180());
        if (0x20 > ret0.length) {
        }
    }
    
    /// @custom:selector    0x7e4174fc
    /// @custom:signature   Unresolved_7e4174fc(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_7e4174fc(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_c[var_a];
    }
    
    /// @custom:selector    0xe634384f
    /// @custom:signature   Unresolved_e634384f(uint256 arg0) public view returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_e634384f(uint256 arg0) public view returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        return abi.encodePacked(address(storage_map_c[var_a]), uint48(storage_map_c[var_a] >> 0xa0), storage_map_c[var_a] >> 0xd0, storage_map_ac[var_a]);
    }
    
    /// @custom:selector    0x138e9de2
    /// @custom:signature   Unresolved_138e9de2() public view
    function Unresolved_138e9de2() public view {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0);
        if (address(unresolved_a69a2ad1) > (address(unresolved_a69a2ad1) + (unresolved_a69a2ad1 >> 0x80))) {
        }
    }
    
    /// @custom:selector    0xc8372577
    /// @custom:signature   Unresolved_c8372577(uint32 arg0) public view returns (bool)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_c8372577(uint32 arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        uint32 var_a = uint32(arg0);
        return abi.encodePacked(!(!bytes1(storage_map_c[var_a])), uint64(storage_map_c[var_a] >> 0x08), uint64(storage_map_c[var_a] >> 0x48), uint64(storage_map_c[var_a] >> 0x88));
    }
    
    /// @custom:selector    0x50c23fab
    /// @custom:signature   Unresolved_50c23fab(uint256 arg0) public view returns (uint64)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_50c23fab(uint256 arg0) public view returns (uint64) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        var_a = uint32(storage_map_c[var_a] >> 0xa0);
        require(!uint32(storage_map_ac[var_a] >> 0x80));
        require(!bytes1(storage_map_ac[var_a] >> 0xe0));
        require(uint64(storage_map_c[var_a] >> 0xc0) - (uint64(storage_map_c[var_a] >> 0xc0) / (uint32(storage_map_ac[var_a] >> 0x80))) > (uint64(storage_map_c[var_a] >> 0xc0)));
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(!(uint64(storage_map_c[var_a] >> 0xc0) - (uint64(storage_map_c[var_a] >> 0xc0) / (uint32(storage_map_ac[var_a] >> 0x80))) * (uint64(storage_map_ac[var_a] >> 0x78)) / (uint64(storage_map_c[var_a] >> 0xc0) - (uint64(storage_map_c[var_a] >> 0xc0) / (uint32(storage_map_ac[var_a] >> 0x80)))) == (uint64(storage_map_ac[var_a] >> 0x78))) | (!(uint64(storage_map_c[var_a] >> 0xc0)) - (uint64(storage_map_c[var_a] >> 0xc0) / (uint32(storage_map_ac[var_a] >> 0x80)))));
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(uint64(storage_map_c[var_a] >> 0xc0) - (uint64(storage_map_c[var_a] >> 0xc0) / (uint32(storage_map_ac[var_a] >> 0x80))) > (uint64(storage_map_c[var_a] >> 0xc0) - (uint64(storage_map_c[var_a] >> 0xc0) / (uint32(storage_map_ac[var_a] >> 0x80))) + (uint64(storage_map_c[var_a] >> 0xc0) - (uint64(storage_map_c[var_a] >> 0xc0) / (uint32(storage_map_ac[var_a] >> 0x80))) * (uint64(storage_map_ac[var_a] >> 0x78)) / 0x0de0b6b3a7640000)));
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        return uint64((storage_map_c[var_a] >> 0xc0) - ((storage_map_c[var_a] >> 0xc0) / (uint32(uint32(storage_map_ac[var_a] >> 0x80)))) + ((storage_map_c[var_a] >> 0xc0) - ((storage_map_c[var_a] >> 0xc0) / (uint32(uint32(storage_map_ac[var_a] >> 0x80)))) * (storage_map_ac[var_a] >> 0x78) / 0x0de0b6b3a7640000));
        require(uint64(storage_map_c[var_a] >> 0xc0) > (uint64(storage_map_c[var_a] >> 0xc0) + (uint64(storage_map_c[var_a] >> 0xc0) / (uint32(storage_map_ac[var_a] >> 0x80)))));
    }
    
    /// @custom:selector    0x63ca348f
    /// @custom:signature   Unresolved_63ca348f(uint32 arg0, uint256 arg1, address arg2, uint32 arg3, uint256 arg4) public pure
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg3 ["uint32", "bytes4", "int32"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    function Unresolved_63ca348f(uint32 arg0, uint256 arg1, address arg2, uint32 arg3, uint256 arg4) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg0 - (uint32(arg0)));
        require(arg1 - arg1);
        require(arg2 - (address(arg2)));
        require(arg3 - (uint32(arg3)));
        require(arg4 - arg4);
    }
    
    /// @custom:selector    0xd188c049
    /// @custom:signature   Unresolved_d188c049(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_d188c049(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_8da5cb5be = (address(arg0)) | (uint96(unresolved_8da5cb5be));
        emit Event_3cfda8ee(address(arg0));
        return ;
    }
    
    /// @custom:selector    0xf2fde38b
    /// @custom:signature   Unresolved_f2fde38b(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_f2fde38b(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_8da5cb5b = (address(arg0 << 0x10)) | (uint96(unresolved_8da5cb5b));
        emit Event_4ffd725f(address(arg0));
        return ;
    }
    
    /// @custom:selector    0xf37d3c4f
    /// @custom:signature   Unresolved_f37d3c4f(uint32 arg0) public view returns (bytes memory)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    function Unresolved_f37d3c4f(uint32 arg0) public view returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (uint32(arg0)));
        uint32 var_a = uint32(arg0);
        return abi.encodePacked(uint96(storage_map_c[var_a]), uint96(storage_map_c[var_a] >> 0x60), storage_map_c[var_a] >> 0xc0, address(storage_map_ac[var_a]), (storage_map_ac[var_a]) >> 0x80);
    }
    
    /// @custom:selector    0x31a4956c
    /// @custom:signature   Unresolved_31a4956c(address arg0) public view returns (bool)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_31a4956c(address arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return abi.encodePacked(storage_map_c[var_a], uint64(storage_map_c[var_a]), uint64(storage_map_c[var_a] >> 0x40), uint32(storage_map_c[var_a] >> 0x80));
    }
    
    /// @custom:selector    0x01681a62
    /// @custom:signature   Unresolved_01681a62(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_01681a62(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        require(!storage_map_c[var_a]);
        require(!address(unresolved_c10f1a75));
        address var_d = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_c10f1a75).Unresolved_c1a9a508(var_d); // staticcall
        require(!0, CustomError_d26ffacb());
        var_a = address(arg0);
        require(!storage_map_c[var_a], CustomError_d26ffacb());
        require(!(block.number > (uint32(storage_map_c[var_a] >> 0x80))), CustomError_d26ffacb());
        var_c = 0x40;
        require(((var_g + 0x60) < var_g) | ((var_g + 0x60) > 0xffffffffffffffff), CustomError_0a9e0180());
        uint256 var_g = var_g + 0x60;
        (bool success, bytes memory ret0) = address(0x0801).Unresolved_00000000(var_i, var_j); // staticcall
        require(!ret0.length, CustomError_0a9e0180());
        require(((0x60 + var_l) - 0x60) < 0x60);
        require(var_c - (uint64(var_c)));
        require(var_l < 0x60, CustomError_0a9e0180());
        require(ret0.length > 0xffffffffffffffff, CustomError_0a9e0180());
        require(((var_g + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) < var_g) | ((var_g + (uint248((0x20 + (ret0.length + 0x1f)) + 0x1f))) > 0xffffffffffffffff), CustomError_0a9e0180());
        if (0x20 > ret0.length) {
        }
        require(!address(unresolved_c10f1a75));
        var_d = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_c10f1a75).Unresolved_c1a9a508(var_d, var_i); // staticcall
        require(!0, CustomError_28ef4314());
        var_a = address(arg0);
        require(storage_map_c[var_a], CustomError_28ef4314());
        var_a = 0;
        require(!(block.number > storage_map_c[var_a]), CustomError_fefe83a0());
        if (0x20 > ret0.length) {
        }
    }
    
    /// @custom:selector    0x1afd17e9
    /// @custom:signature   Unresolved_1afd17e9(uint32 arg0, uint256 arg1, address arg2, uint32 arg3) public pure
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg3 ["uint32", "bytes4", "int32"]
    function Unresolved_1afd17e9(uint32 arg0, uint256 arg1, address arg2, uint32 arg3) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x80);
        require(arg0 - (uint32(arg0)));
        require(arg1 - arg1);
        require(arg2 - (address(arg2)));
        require(arg3 - (uint32(arg3)));
    }
    
    /// @custom:selector    0x628a9fd6
    /// @custom:signature   Unresolved_628a9fd6(uint32 arg0, address arg1, address arg2) public payable returns (uint256)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    /// @param              arg1 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg2 ["address", "uint128", "bytes16", "int128"]
    function Unresolved_628a9fd6(uint32 arg0, address arg1, address arg2) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (uint32(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
        require(!(msg.sender == (address(unresolved_8da5cb5b >> 0x10))), CustomError_989c4c7c());
        require(!(msg.sender == (address(unresolved_21f55a6c))), CustomError_989c4c7c());
        require(!(uint32(arg0) < (uint32(unresolved_f28bbdb2))), CustomError_67207a88());
        uint32 var_b = uint32(arg0);
        storage_map_h[var_b] = (address(arg1)) | (address(arg2 << 0x80));
        emit Event_a065d6ba(uint32(arg0), address(arg1), address(arg2));
        return ;
    }
    
    /// @custom:selector    0xae4daf4e
    /// @custom:signature   Unresolved_ae4daf4e(address arg0, uint256 arg1, uint256 arg2) public payable returns (bytes memory)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_ae4daf4e(address arg0, uint256 arg1, uint256 arg2) public payable returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        var_b = 0x0f;
        (bool success, bytes memory ret0) = address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).Unresolved_2448a553(var_b); // delegatecall
        return abi.encodePacked(0, 0, 0);
        require(0x60 > ret0.length);
        require(((var_i + 0x60) < var_i) | ((var_i + 0x60) > 0xffffffffffffffff));
        uint256 var_i = var_i + 0x60;
        require(((var_i + 0x60) - var_i) < 0x60);
        return abi.encodePacked(var_i.length, var_q, var_r);
    }
    
    /// @custom:selector    0xe53e3de6
    /// @custom:signature   Unresolved_e53e3de6(address arg0, uint256 arg1) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_e53e3de6(address arg0, uint256 arg1) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x40);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_e1f9209b)), CustomError_538ccdfd());
        require(!arg1, CustomError_f4d678b8());
        address var_b = msg.sender;
        require(storage_map_g[var_b] < arg1, CustomError_f4d678b8());
        var_b = msg.sender;
        storage_map_g[var_b] = storage_map_g[var_b] - arg1;
        var_b = address(arg0);
        require(storage_map_g[var_b] > (storage_map_g[var_b] + arg1));
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        storage_map_g[var_b] = storage_map_g[var_b] + arg1;
        emit Event_e7fd56ed(address(arg0), arg1);
        return ;
        return ;
    }
    
    /// @custom:selector    0x88f2aea5
    /// @custom:signature   Unresolved_88f2aea5() public payable returns (uint256)
    function Unresolved_88f2aea5() public payable returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0);
        require(msg.sender - (address(unresolved_cbeb5f3d)), CustomError_2d016ae6());
        require(!unresolved_afdf6702 >> 0x80);
        unresolved_afdf6702 = address(unresolved_afdf6702);
        require(unresolved_53ac4b66);
        require(!0 < (unresolved_afdf6702 >> 0x80));
        require(0);
        address var_b = address(unresolved_cbeb5f3d);
        require(storage_map_g[var_b] > (storage_map_g[var_b] + 0));
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        storage_map_g[var_b] = storage_map_g[var_b] + 0;
        require((address(unresolved_a69a2ad1) + 0) > 0xffffffffffffffffffffffffffffffff);
        unresolved_a69a2ad1 = (address(unresolved_a69a2ad1 + 0)) | (address(unresolved_a69a2ad1));
        require(0 < (unresolved_afdf6702 >> 0x80));
        require(!address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).code.length);
        var_e = 0x0f;
        (bool success, bytes memory ret0) = address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).Unresolved_18958ce2(var_e); // delegatecall
        emit Event_8163d4e6(address(unresolved_cbeb5f3d), unresolved_afdf6702 >> 0x80, 0);
        return ;
        if (var_i > 0xffffffffffffffff) {
            emit Event_8163d4e6(address(unresolved_cbeb5f3d), unresolved_afdf6702 >> 0x80, 0);
            return ;
            emit Event_8163d4e6(address(unresolved_cbeb5f3d), unresolved_afdf6702 >> 0x80, 0);
            return ;
            return ;
        }
    }
    
    /// @custom:selector    0xa0bf0f75
    /// @custom:signature   Unresolved_a0bf0f75(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_a0bf0f75(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_ed410ee1 = (address(arg0)) | (uint96(unresolved_ed410ee1));
        emit Event_af809937(address(arg0));
        return ;
    }
    
    /// @custom:selector    0x6a3214c9
    /// @custom:signature   Unresolved_6a3214c9(address arg0, uint256 arg1) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_6a3214c9(address arg0, uint256 arg1) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x40);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        address var_b = address(arg0);
        require(storage_map_g[var_b], CustomError_28ef4314());
        require(!(((arg1 * unresolved_ec0bdcfc) / arg1) == unresolved_ec0bdcfc) | !arg1);
        require(!arg1 * unresolved_ec0bdcfc);
        var_b = address(arg0);
        require(storage_map_g[var_b] > (storage_map_g[var_b] + (arg1 * unresolved_ec0bdcfc)));
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        storage_map_g[var_b] = storage_map_g[var_b] + (arg1 * unresolved_ec0bdcfc);
        require(address(unresolved_a69a2ad1) + (address(arg1 * unresolved_ec0bdcfc)) > 0xffffffffffffffffffffffffffffffff);
        return ;
    }
    
    /// @custom:selector    0xa25dc87f
    /// @custom:signature   Unresolved_a25dc87f(address arg0) public view returns (bytes memory)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_a25dc87f(address arg0) public view returns (bytes memory) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        var_a = keccak256(var_a);
        require(0 < storage_map_c[var_a]);
        require(((var_d + (uint248(((var_d + 0x20) - var_d) + 0x1f))) < var_d) | ((var_d + (uint248(((var_d + 0x20) - var_d) + 0x1f))) > 0xffffffffffffffff));
        uint248 var_d = var_d + (uint248(((var_d + 0x20) - var_d) + 0x1f));
        return abi.encodePacked(0x20, var_d.length);
    }
    
    /// @custom:selector    0xd7c7e5fb
    /// @custom:signature   Unresolved_d7c7e5fb(uint32 arg0, uint32 arg1, address arg2) public payable returns (uint256)
    /// @param              arg0 ["uint32", "bytes4", "int32"]
    /// @param              arg1 ["uint32", "bytes4", "int32"]
    /// @param              arg2 ["address", "uint120", "bytes15", "int120"]
    function Unresolved_d7c7e5fb(uint32 arg0, uint32 arg1, address arg2) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (uint32(arg0)));
        require(arg1 - (uint32(arg1)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        require(!(uint32(arg0) < (uint32(unresolved_f28bbdb2))), CustomError_b0cb274d());
        require(!(!uint32(arg1)), CustomError_b0cb274d());
        require(!arg2, CustomError_b0cb274d());
        require(arg2 > 0xffffffffffffffffffffffffffffff, CustomError_b0cb274d());
        uint32 var_b = uint32(arg0);
        storage_map_g[var_b] = (uint32(arg1 << 0xe0)) | (uint224(storage_map_g[var_b]));
        storage_map_h[var_b] = (address(arg2)) | (address(storage_map_h[var_b]));
        emit Event_62db1b2b(uint32(arg0), uint32(arg1), arg2);
        return ;
    }
    
    /// @custom:selector    0x753a369c
    /// @custom:signature   Unresolved_753a369c(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_753a369c(address arg0, uint256 arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x80);
        require(arg0 - (address(arg0)));
        var_b = 0x0f;
        (bool success, bytes memory ret0) = address(0x5a4bda2dcc82749258d9e5cdd49cd52c3cd16388).Unresolved_3cf4208d(var_b); // delegatecall
        return abi.encodePacked(0, 0, 0);
        require(0x60 > ret0.length);
        require(((var_j + 0x60) < var_j) | ((var_j + 0x60) > 0xffffffffffffffff));
        uint256 var_j = var_j + 0x60;
        require(((var_j + 0x60) - var_j) < 0x60);
        return abi.encodePacked(var_j.length, var_r, var_s);
    }
    
    /// @custom:selector    0x8d09f23f
    /// @custom:signature   Unresolved_8d09f23f(address arg0, uint256 arg1, uint256 arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint64", "bytes8", "int64"]
    /// @param              arg4 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    /// @param              arg6 ["uint256", "bytes32", "int256"]
    function Unresolved_8d09f23f(address arg0, uint256 arg1, uint256 arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xe0);
        require(arg0 - (address(arg0)));
        require(arg3 - (uint64(arg3)));
        require(arg4 - (bytes1(arg4)));
        require(!(address(arg0)), CustomError_4f57ffae());
        address var_a = address(arg0);
        require(!(block.number > storage_map_c[var_a]), CustomError_4f57ffae());
        require(!address(unresolved_53e23e2e >> 0x08).code.length);
        address var_d = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_53e23e2e >> 0x08).Unresolved_b002b9fa(var_d); // call
        require(((var_l + 0xc0) > 0xffffffffffffffff) | ((var_l + 0xc0) < var_l));
        uint256 var_l = var_l + 0xc0;
        var_o = keccak256(var_p);
        (bool success, bytes memory ret0) = address(unresolved_53e23e2e >> 0x08).Unresolved_d45167d0(var_o); // staticcall
        require(0, CustomError_c20280ea());
        require(!(0 == (address(arg0))), CustomError_c20280ea());
        require(!((((arg1 * unresolved_ec0bdcfc) / arg1) == unresolved_ec0bdcfc) | !arg1), CustomError_c20280ea());
        require(!0, CustomError_c20280ea());
        require(0x20 > ret0.length);
        require(((var_l + 0x20) < var_l) | ((var_l + 0x20) > 0xffffffffffffffff));
        var_l = var_l + 0x20;
        require(((var_l + 0x20) - var_l) < 0x20);
        if (var_l.length - (address(var_l.length))) {
            require(var_l.length - (address(var_l.length)));
        }
        require(var_l > 0xffffffffffffffff);
        require(0);
    }
    
    /// @custom:selector    0xefc1bd46
    /// @custom:signature   Unresolved_efc1bd46(address arg0) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_efc1bd46(address arg0) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b >> 0x10)), CustomError_30cd7471());
        unresolved_9d47d4d3 = (address(arg0)) | (uint96(unresolved_9d47d4d3));
        emit Event_abf32d7c(address(arg0));
        return ;
    }
    
    /// @custom:selector    0xf84a74d3
    /// @custom:signature   Unresolved_f84a74d3(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_f84a74d3(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_c[var_a];
    }
    
    /// @custom:selector    0x99fbab88
    /// @custom:signature   Unresolved_99fbab88(uint256 arg0) public view returns (bool)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_99fbab88(uint256 arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        uint256 var_a = arg0;
        return abi.encodePacked(address(storage_map_c[var_a]), uint32(storage_map_c[var_a] >> 0xa0), storage_map_c[var_a] >> 0xc0, address(storage_map_ac[var_a]), uint32(storage_map_ac[var_a] >> 0x80), uint64(storage_map_ac[var_a] >> 0xa0), !(!bytes1(storage_map_ac[var_a] >> 0xe0)), !(!bytes1(storage_map_ac[var_a] >> 0xe8)), (bytes1(storage_map_ac[var_a] >> 0xf0)));
    }
    
    /// @custom:selector    0x415f1240
    /// @custom:signature   Unresolved_415f1240(uint256 arg0) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    function Unresolved_415f1240(uint256 arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(((var_a + 0x20) > 0xffffffffffffffff) | ((var_a + 0x20) < var_a));
        uint256 var_a = var_a + 0x20;
        require(((var_a + 0x20) > 0xffffffffffffffff) | ((var_a + 0x20) < var_a));
        var_a = var_a + 0x20;
        uint256 var_b = arg0;
        require(!bytes1(storage_map_h[var_b] >> 0xf0));
        var_b = uint32(storage_map_g[var_b] >> 0xa0);
        require(uint32(storage_map_g[var_b] >> 0xa0) < var_a.length);
        require(!(uint32(storage_map_g[var_b] >> 0xa0)) < var_a.length);
        require(!(uint32(storage_map_g[var_b] >> 0xa0)) < var_a.length);
        require(!var_g);
        var_b = uint32(storage_map_g[var_b] >> 0xa0);
        require(bytes1(storage_map_g[var_b]));
        require(uint64(storage_map_g[var_b] >> 0x08) > (uint64(storage_map_g[var_b] >> 0x08) + (uint64(storage_map_g[var_b] >> 0x48))));
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(!(uint32(storage_map_g[var_b] >> 0xa0)) < var_a.length);
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        uint256 var_i = uint32(storage_map_g[var_b] >> 0xc0);
        (bool success, bytes memory ret0) = address(unresolved_7dc0d1d0).Unresolved_c0182669(var_i); // staticcall
        require(0x20 > ret0.length);
        require(((var_a + 0x20) < var_a) | ((var_a + 0x20) > 0xffffffffffffffff));
        var_a = var_a + 0x20;
        require(((var_a + 0x20) - var_a) < 0x20);
        require(var_a.length - (uint64(var_a.length)));
    }
}