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
    bytes public constant unresolved_4e71d92d = a15ce1ba;
    bytes public constant unresolved_e4fc6b6d = a15ce1ba;
    uint256 public constant unresolved_5638b3e5 = 16261592980719540282406543360114735616254807997602652632677330415238910058074;
    uint256 public constant unresolved_89ee09f0 = 6594604465550134414809898413287372025719474358590716135486021108148331669680;
    uint256 public constant unresolved_6b0509b1 = 69146583506332244320030642255554849150605785262217336600759584127041064968079;
    uint256 public constant unresolved_0700cc42 = 13930892446639198898740963613098559602520106960297502542262608917341054151118;
    bytes public constant unresolved_2e17de78 = ;
    bytes public constant unresolved_a694fc3a = ;
    
    mapping(bytes32 => bytes32) storage_map_l;
    mapping(bytes32 => bytes32) storage_map_c;
    address public unresolved_f7c618c1;
    uint256 public unresolved_2b6fdc7e;
    uint256 public unresolved_cab64bcd;
    address public unresolved_d2f7265a;
    uint256 public unresolved_3644e515;
    address public unresolved_51ed6a30;
    bool public unresolved_6090cf16;
    bytes32 store_b;
    address public unresolved_8da5cb5b;
    bytes32 store_i;
    bytes32 store_g;
    uint256 public unresolved_817b1cd2;
    uint256 public unresolved_939d6237;
    
    event Event_4ffd725f();
    event Event_f7576d8c();
    error CustomError_00000000();
    event Event_3cfda8ee();
    event Event_3fde1edb();
    
    /// @custom:selector    0x83115825
    /// @custom:signature   Unresolved_83115825(address arg0, uint256 arg1, bool arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg3 ["uint64", "bytes8", "int64"]
    /// @param              arg4 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    /// @param              arg6 ["uint256", "bytes32", "int256"]
    function Unresolved_83115825(address arg0, uint256 arg1, bool arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xe0);
        require(arg0 - (address(arg0)));
        require(arg3 - (uint64(arg3)));
        require(arg4 - (bytes1(arg4)));
        require(msg.sender - (address(unresolved_6090cf16)), CustomError_da96f0b6());
        require(store_b - 0x01, CustomError_756688fe());
        store_b = 0x02;
        var_b = var_b;
        bool var_f = arg2;
        require(((var_h + 0xc0) > 0xffffffffffffffff) | ((var_h + 0xc0) < var_h), CustomError_756688fe());
        uint256 var_h = var_h + 0xc0;
        require(block.timestamp > (uint64(arg3)), CustomError_756688fe());
        var_b = var_f >> 0x08;
        require(storage_map_c[var_b] & (0x01 << (bytes1(arg2))), CustomError_756688fe());
        var_b = var_f >> 0x08;
        storage_map_c[var_b] = storage_map_c[var_b] | (0x01 << (bytes1(arg2)));
        var_b = address(arg0);
        require(!(arg2 < storage_map_c[var_b]), CustomError_8baa579f());
        emit Event_3fde1edb(address(arg0), arg2, storage_map_c[var_b]);
        require(((var_h + 0xc0) > 0xffffffffffffffff) | ((var_h + 0xc0) < var_h), CustomError_8baa579f());
        var_h = var_h + 0xc0;
        require(((var_h + 0x80) > 0xffffffffffffffff) | ((var_h + 0x80) < var_h), CustomError_8baa579f());
        var_h = var_h + 0x80;
        require(!(bytes1(arg4) == 0x1b), CustomError_8baa579f());
        require(!(bytes1(arg4) == 0x1b), CustomError_8baa579f());
        require(arg6 > 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0, CustomError_8baa579f());
        require(0, CustomError_8baa579f());
        require(!(0 == (address(arg0))), CustomError_8baa579f());
        require(!arg1);
        var_b = address(arg0);
        require(!((storage_map_c[var_b] * unresolved_939d6237) / storage_map_c[var_b] == unresolved_939d6237) | !storage_map_c[var_b]);
        var_b = address(arg0);
        require(((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) > storage_map_c[var_b]);
        require(((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_c[var_b] > ((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000));
        var_b = address(arg0);
        var_j = 0x0b;
        require(storage_map_c[var_b] > (storage_map_c[var_b] + (((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_c[var_b])));
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        storage_map_c[var_b] = storage_map_c[var_b] + (((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_c[var_b]);
        address var_w = address(arg0);
        (bool success, bytes memory ret0) = address(unresolved_51ed6a30).Unresolved_23b872dd(var_w); // call
        require(!0, CustomError_90b8ec18());
        require(0x20 > ret0.length);
        require(((var_h + 0x20) < var_h) | ((var_h + 0x20) > 0xffffffffffffffff));
        var_h = var_h + 0x20;
        require(((var_h + 0x20) - var_h) < 0x20);
        require(var_h.length - var_h.length, CustomError_90b8ec18());
        require(!var_h.length, CustomError_90b8ec18());
        require(!0, CustomError_8baa579f());
        require(!var_j);
        require(arg2 > (arg2 + 0x01), CustomError_f87d9271());
    }
    
    /// @custom:selector    0x9c96d4a1
    /// @custom:signature   Unresolved_9c96d4a1(address arg0, bool arg1, uint64 arg2, bool arg3, uint256 arg4, uint256 arg5) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg2 ["uint64", "bytes8", "int64"]
    /// @param              arg3 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    function Unresolved_9c96d4a1(address arg0, bool arg1, uint64 arg2, bool arg3, uint256 arg4, uint256 arg5) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xc0);
        require(arg0 - (address(arg0)));
        require(arg2 - (uint64(arg2)));
        require(arg3 - (bytes1(arg3)));
        require(msg.sender - (address(unresolved_6090cf16)), CustomError_da96f0b6());
        require(store_b - 0x01, CustomError_756688fe());
        store_b = 0x02;
        var_b = var_b;
        bool var_e = arg1;
        require(((var_g + 0xa0) > 0xffffffffffffffff) | ((var_g + 0xa0) < var_g), CustomError_756688fe());
        uint256 var_g = var_g + 0xa0;
        require(block.timestamp > (uint64(arg2)), CustomError_756688fe());
        var_b = var_e >> 0x08;
        require(storage_map_c[var_b] & (0x01 << (bytes1(arg1))), CustomError_756688fe());
        var_b = var_e >> 0x08;
        storage_map_c[var_b] = storage_map_c[var_b] | (0x01 << (bytes1(arg1)));
        var_b = address(arg0);
        require(!(arg1 < storage_map_c[var_b]), CustomError_8baa579f());
        emit Event_3fde1edb(address(arg0), arg1, storage_map_c[var_b]);
        require(((var_g + 0xc0) > 0xffffffffffffffff) | ((var_g + 0xc0) < var_g), CustomError_8baa579f());
        var_g = var_g + 0xc0;
        require(((var_g + 0x80) > 0xffffffffffffffff) | ((var_g + 0x80) < var_g), CustomError_8baa579f());
        require(!(bytes1(arg3) == 0x1b), CustomError_8baa579f());
        require(!(bytes1(arg3) == 0x1b), CustomError_8baa579f());
        require(arg5 > 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0, CustomError_8baa579f());
        require(0, CustomError_8baa579f());
        require(!(0 == (address(arg0))), CustomError_8baa579f());
        var_b = address(arg0);
        require(!(((storage_map_c[var_b] * unresolved_939d6237) / storage_map_c[var_b] == unresolved_939d6237) | !storage_map_c[var_b]), CustomError_8baa579f());
        var_b = address(arg0);
        require(((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) > storage_map_c[var_b], CustomError_8baa579f());
        require(((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_c[var_b] > ((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000), CustomError_8baa579f());
        var_b = address(arg0);
        var_i = 0x0b;
        require(storage_map_c[var_b] > (storage_map_c[var_b] + (((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_c[var_b])), CustomError_8baa579f());
        require(!0, CustomError_8baa579f());
        require(!var_i);
        require(arg1 > (arg1 + 0x01), CustomError_f87d9271());
    }
    
    /// @custom:selector    0x0f71c8bc
    /// @custom:signature   Unresolved_0f71c8bc(address arg0, address arg1) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_0f71c8bc(address arg0, address arg1) public payable {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(msg.sender - (address(store_g)), CustomError_c031a0df());
        require(!(bytes1(unresolved_6090cf16 >> 0xa0)), CustomError_3f733c4f());
        require(bytes1(unresolved_6090cf16 >> 0xa0), CustomError_3f733c4f());
        require(!(address(arg0)), CustomError_904bc503());
        unresolved_8da5cb5b = (address(arg0)) | (uint96(unresolved_8da5cb5b));
        unresolved_6090cf16 = 0x010000000000000000000000000000000000000000 | (address(arg1) | (uint88(unresolved_6090cf16)));
        emit Event_4ffd725f(address(arg0));
        emit Event_3cfda8ee(address(arg1));
    }
    
    /// @custom:selector    0x9ccae24e
    /// @custom:signature   Unresolved_9ccae24e(address arg0, address arg1, address arg2, address arg3, address arg4) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg3 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg4 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_9ccae24e(address arg0, address arg1, address arg2, address arg3, address arg4) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
        require(arg3 - (address(arg3)));
        require(arg4 - (address(arg4)));
        require(bytes1(store_i), CustomError_904bc503());
        require(!(bytes1(store_i >> 0x08)), CustomError_904bc503());
        require(!(bytes1(store_i >> 0x08)), CustomError_904bc503());
        unresolved_d2f7265a = (uint96(unresolved_d2f7265a)) | (address(arg0));
        unresolved_51ed6a30 = (uint96(unresolved_51ed6a30)) | (address(arg1));
        unresolved_f7c618c1 = (uint96(unresolved_f7c618c1)) | (address(arg2));
        store_b = 0x01;
        require(!(address(arg3)), CustomError_904bc503());
        unresolved_8da5cb5b = (address(arg3)) | (uint96(unresolved_8da5cb5b));
        unresolved_6090cf16 = 0x010000000000000000000000000000000000000000 | (address(arg4) | (uint88(unresolved_6090cf16)));
        require(((var_g + 0xc0) > 0xffffffffffffffff) | ((var_g + 0xc0) < var_g), CustomError_904bc503());
        unresolved_3644e515 = keccak256(var_j);
        emit Event_4ffd725f(address(arg3));
        emit Event_3cfda8ee(address(arg4));
        require(!(bytes1(store_i >> 0x08)), CustomError_904bc503());
        store_i = uint248(store_i);
        require(bytes1(store_i), CustomError_0dc149f0());
    }
    
    /// @custom:selector    0xf2f59776
    /// @custom:signature   Unresolved_f2f59776(address arg0, uint256 arg1) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_f2f59776(address arg0, uint256 arg1) public view returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        var_a = arg1;
        return storage_map_l[var_a];
    }
    
    /// @custom:selector    0xfa2871b5
    /// @custom:signature   Unresolved_fa2871b5(address arg0, uint256 arg1, bool arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg3 ["uint64", "bytes8", "int64"]
    /// @param              arg4 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    /// @param              arg6 ["uint256", "bytes32", "int256"]
    function Unresolved_fa2871b5(address arg0, uint256 arg1, bool arg2, uint64 arg3, bool arg4, uint256 arg5, uint256 arg6) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xe0);
        require(arg0 - (address(arg0)));
        require(arg3 - (uint64(arg3)));
        require(arg4 - (bytes1(arg4)));
        require(msg.sender - (address(unresolved_6090cf16)), CustomError_da96f0b6());
        require(store_b - 0x01, CustomError_756688fe());
        store_b = 0x02;
        var_b = var_b;
        bool var_f = arg2;
        require(((var_h + 0xc0) > 0xffffffffffffffff) | ((var_h + 0xc0) < var_h), CustomError_756688fe());
        uint256 var_h = var_h + 0xc0;
        require(block.timestamp > (uint64(arg3)), CustomError_756688fe());
        var_b = var_f >> 0x08;
        require(storage_map_c[var_b] & (0x01 << (bytes1(arg2))), CustomError_756688fe());
        var_b = var_f >> 0x08;
        storage_map_c[var_b] = storage_map_c[var_b] | (0x01 << (bytes1(arg2)));
        var_b = address(arg0);
        require(!(arg2 < storage_map_c[var_b]), CustomError_8baa579f());
        emit Event_3fde1edb(address(arg0), arg2, storage_map_c[var_b]);
        require(((var_h + 0xc0) > 0xffffffffffffffff) | ((var_h + 0xc0) < var_h), CustomError_8baa579f());
        var_h = var_h + 0xc0;
        require(((var_h + 0x80) > 0xffffffffffffffff) | ((var_h + 0x80) < var_h), CustomError_8baa579f());
        require(!(bytes1(arg4) == 0x1b), CustomError_8baa579f());
        require(!(bytes1(arg4) == 0x1b), CustomError_8baa579f());
        require(arg6 > 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0, CustomError_8baa579f());
        require(0, CustomError_8baa579f());
        require(!(0 == (address(arg0))), CustomError_8baa579f());
        require(!arg1, CustomError_f1bc94d2());
        var_b = address(arg0);
        require(storage_map_c[var_b] < arg1, CustomError_f1bc94d2());
        var_b = address(arg0);
        require(!(((storage_map_c[var_b] * unresolved_939d6237) / storage_map_c[var_b] == unresolved_939d6237) | !storage_map_c[var_b]), CustomError_1f2a2005());
        var_b = address(arg0);
        require(((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) > storage_map_c[var_b], CustomError_1f2a2005());
        require(((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_c[var_b] > ((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000), CustomError_1f2a2005());
        var_b = address(arg0);
        var_j = 0x0b;
        require(storage_map_c[var_b] > (storage_map_c[var_b] + (((storage_map_c[var_b] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_c[var_b])), CustomError_1f2a2005());
        require(!0, CustomError_8baa579f());
        require(!var_j);
        require(arg2 > (arg2 + 0x01), CustomError_f87d9271());
    }
    
    /// @custom:selector    0x31d7a262
    /// @custom:signature   Unresolved_31d7a262(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_31d7a262(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_l[var_a];
    }
    
    /// @custom:selector    0x7ecebe00
    /// @custom:signature   Unresolved_7ecebe00(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_7ecebe00(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_l[var_a];
    }
    
    /// @custom:selector    0xf40f0f52
    /// @custom:signature   Unresolved_f40f0f52(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_f40f0f52(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        require(!((storage_map_l[var_a] * unresolved_939d6237) / storage_map_l[var_a] == unresolved_939d6237) | !storage_map_l[var_a]);
        var_a = address(arg0);
        require(((storage_map_l[var_a] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) > storage_map_l[var_a]);
        require(((storage_map_l[var_a] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_l[var_a] > ((storage_map_l[var_a] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000));
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        require(storage_map_l[var_a] > (storage_map_l[var_a] + (((storage_map_l[var_a] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_l[var_a])));
        var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        return storage_map_l[var_a] + (((storage_map_l[var_a] * unresolved_939d6237) / 0x033b2e3c9fd0803ce8000000) - storage_map_l[var_a]);
        return storage_map_l[var_a];
    }
    
    /// @custom:selector    0xd188c049
    /// @custom:signature   Unresolved_d188c049(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_d188c049(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        unresolved_6090cf16 = (uint96(unresolved_6090cf16)) | (address(arg0));
        emit Event_3cfda8ee(address(arg0));
    }
    
    /// @custom:selector    0xf2fde38b
    /// @custom:signature   Unresolved_f2fde38b(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_f2fde38b(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        unresolved_8da5cb5b = (address(arg0)) | (uint96(unresolved_8da5cb5b));
        emit Event_4ffd725f(address(arg0));
    }
    
    /// @custom:selector    0x5873eb9b
    /// @custom:signature   Unresolved_5873eb9b(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_5873eb9b(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_l[var_a];
    }
    
    /// @custom:selector    0x60217267
    /// @custom:signature   Unresolved_60217267(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_60217267(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_l[var_a];
    }
    
    /// @custom:selector    0xf0355460
    /// @custom:signature   Unresolved_f0355460(address arg0, bool arg1, uint64 arg2, bool arg3, uint256 arg4, uint256 arg5) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg2 ["uint64", "bytes8", "int64"]
    /// @param              arg3 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    function Unresolved_f0355460(address arg0, bool arg1, uint64 arg2, bool arg3, uint256 arg4, uint256 arg5) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xc0);
        require(arg0 - (address(arg0)));
        require(arg2 - (uint64(arg2)));
        require(arg3 - (bytes1(arg3)));
        require(msg.sender - (address(unresolved_6090cf16)), CustomError_da96f0b6());
        require(store_b - 0x01, CustomError_756688fe());
        store_b = 0x02;
        var_b = var_b;
        bool var_e = arg1;
        require(((var_g + 0xa0) > 0xffffffffffffffff) | ((var_g + 0xa0) < var_g), CustomError_756688fe());
        uint256 var_g = var_g + 0xa0;
        require(block.timestamp > (uint64(arg2)), CustomError_756688fe());
        var_b = var_e >> 0x08;
        require(storage_map_c[var_b] & (0x01 << (bytes1(arg1))), CustomError_756688fe());
        var_b = var_e >> 0x08;
        storage_map_c[var_b] = storage_map_c[var_b] | (0x01 << (bytes1(arg1)));
        var_b = address(arg0);
        var_i = 0x0c;
        require(!(arg1 < storage_map_c[var_b]), CustomError_8baa579f());
        emit Event_3fde1edb(address(arg0), arg1, storage_map_c[var_b]);
        require(((var_g + 0xc0) > 0xffffffffffffffff) | ((var_g + 0xc0) < var_g), CustomError_8baa579f());
        var_g = var_g + 0xc0;
        require(((var_g + 0x80) > 0xffffffffffffffff) | ((var_g + 0x80) < var_g), CustomError_8baa579f());
        var_g = var_g + 0x80;
        require(!(bytes1(arg3) == 0x1b), CustomError_8baa579f());
        require(!(bytes1(arg3) == 0x1b), CustomError_8baa579f());
        require(arg5 > 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0, CustomError_8baa579f());
        require(0, CustomError_8baa579f());
        require(!(0 == (address(arg0))), CustomError_8baa579f());
        require(!address(unresolved_d2f7265a).code.length);
        (bool success, bytes memory ret0) = address(unresolved_d2f7265a).Unresolved_7b9f5264(var_v); // call
        address var_v = address(this);
        (bool success, bytes memory ret0) = address(unresolved_d2f7265a).Unresolved_27e235e3(var_v); // staticcall
        if (!0 > unresolved_cab64bcd) {
            if ((0 - unresolved_cab64bcd) > 0) {
                require(!0 > unresolved_cab64bcd);
                require((0 - unresolved_cab64bcd) > 0);
                require(!unresolved_817b1cd2);
                require((0 - unresolved_cab64bcd) > ((0 - unresolved_cab64bcd) + unresolved_2b6fdc7e));
                require((0 - unresolved_cab64bcd) + unresolved_2b6fdc7e);
                unresolved_cab64bcd = unresolved_cab64bcd + (0 - unresolved_cab64bcd);
                unresolved_2b6fdc7e = 0;
                require(unresolved_cab64bcd > (unresolved_cab64bcd + (0 - unresolved_cab64bcd)));
                uint256 var_u = 0;
                emit Event_f7576d8c(0, var_u - unresolved_cab64bcd, (0 - unresolved_cab64bcd) + unresolved_2b6fdc7e, unresolved_939d6237);
                store_b = 0x01;
                return (0 - unresolved_cab64bcd) + unresolved_2b6fdc7e;
                require(!((((0 - unresolved_cab64bcd) + unresolved_2b6fdc7e) * 0x033b2e3c9fd0803ce8000000) / ((0 - unresolved_cab64bcd) + unresolved_2b6fdc7e) == 0x033b2e3c9fd0803ce8000000) | (!(0 - unresolved_cab64bcd) + unresolved_2b6fdc7e));
            }
        }
        require(0x20 > ret0.length);
        require(((var_g + 0x20) < var_g) | ((var_g + 0x20) > 0xffffffffffffffff));
        var_g = var_g + 0x20;
        require(((var_g + 0x20) - var_g) < 0x20);
        if (!var_g.length > unresolved_cab64bcd) {
        }
        require(var_g > 0xffffffffffffffff, CustomError_8baa579f());
        require(!0, CustomError_8baa579f());
        require(!var_i);
        require(arg1 > (arg1 + 0x01), CustomError_f87d9271());
    }
    
    /// @custom:selector    0xcab7e8eb
    /// @custom:signature   Unresolved_cab7e8eb(address arg0, bool arg1) public view returns (bool)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["bool", "uint8", "bytes1", "int8"]
    function Unresolved_cab7e8eb(address arg0, bool arg1) public view returns (bool) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        var_a = arg1 >> 0x08;
        return !(!(storage_map_l[var_a]) & (0x01 << (bytes1(arg1))));
    }
    
    /// @custom:selector    0x78e890ba
    /// @custom:signature   Unresolved_78e890ba() public view returns (uint256)
    function Unresolved_78e890ba() public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0);
        if (((var_g + 0xc0) > 0xffffffffffffffff) | ((var_g + 0xc0) < var_g)) {
            return keccak256(var_k);
        }
    }
    
    /// @custom:selector    0xc0c53b8b
    /// @custom:signature   Unresolved_c0c53b8b(address arg0, address arg1, address arg2) public pure
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_c0c53b8b(address arg0, address arg1, address arg2) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
    }
}