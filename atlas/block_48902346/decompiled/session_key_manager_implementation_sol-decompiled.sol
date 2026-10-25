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
    uint256 public constant unresolved_2bc9ed54 = 95822542117348895877517704542111261115797083880653121026690469309914906226130;
    uint256 public constant unresolved_0b4c3a82 = 77935372474634295659604959651330011782675254592648907581513399052522480669204;
    uint256 public constant unresolved_208e24fc = 70903975225066453318936153029989654653920228574850568705021951009736849476371;
    uint256 public constant unresolved_6525a680 = 114383879396680291043671923856475200043557451592286067796433268579317523523971;
    
    mapping(bytes32 => bytes32) storage_map_d;
    address public unresolved_97dc97cb;
    address public unresolved_8da5cb5b;
    mapping(bytes32 => bytes32) storage_map_b;
    uint256 public unresolved_3644e515;
    
    event Event_3cec0566();
    event Event_4ffd725f();
    event Event_744157cc();
    error CustomError_00000000();
    event Event_f09fcf47();
    event Event_fe60173c();
    
    /// @custom:selector    0x17a1678f
    /// @custom:signature   Unresolved_17a1678f(address arg0, uint64 arg1, address arg2) public pure
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint64", "bytes8", "int64"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_17a1678f(address arg0, uint64 arg1, address arg2) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(uint64(arg1) - arg1);
        require(address(arg2) - arg2);
    }
    
    /// @custom:selector    0xd45167d0
    /// @custom:signature   Unresolved_d45167d0(uint256 arg0, bool arg1, uint256 arg2, uint256 arg3) public payable returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_d45167d0(uint256 arg0, bool arg1, uint256 arg2, uint256 arg3) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x80);
        require(arg1 - (bytes1(arg1)));
        var_b = var_b;
        var_b = var_b;
        require(((var_h + 0xc0) > 0xffffffffffffffff) | ((var_h + 0xc0) < var_h));
        uint256 var_h = var_h + 0xc0;
        require(((var_h + 0x80) > 0xffffffffffffffff) | ((var_h + 0x80) < var_h));
        require(!(bytes1(arg1)) == 0x1b);
        require(!(bytes1(arg1)) == 0x1b);
        require(arg3 > 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0);
        return 0;
        address var_b = ecrecover(keccak256(var_l), bytes1(arg1), arg2, arg3);
        require(!var_s);
        return address(var_b);
        return 0;
    }
    
    /// @custom:selector    0x96ade1f9
    /// @custom:signature   Unresolved_96ade1f9(address arg0, address arg1) public view returns (bytes memory)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_96ade1f9(address arg0, address arg1) public view returns (bytes memory) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        var_a = address(arg1);
        return abi.encodePacked(uint64(storage_map_b[var_a]), address(storage_map_b[var_a] >> 0x40));
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
        return !(!(storage_map_b[var_a]) & (0x01 << (bytes1(arg1))));
    }
    
    /// @custom:selector    0x5f76a1d6
    /// @custom:signature   Unresolved_5f76a1d6(address arg0, address arg1, uint64 arg2, address arg3, bool arg4, uint64 arg5, bool arg6, uint256 arg7, uint256 arg8) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint64", "bytes8", "int64"]
    /// @param              arg3 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg4 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg5 ["uint64", "bytes8", "int64"]
    /// @param              arg6 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg7 ["uint256", "bytes32", "int256"]
    /// @param              arg8 ["uint256", "bytes32", "int256"]
    function Unresolved_5f76a1d6(address arg0, address arg1, uint64 arg2, address arg3, bool arg4, uint64 arg5, bool arg6, uint256 arg7, uint256 arg8) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x0120);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(arg2 - (uint64(arg2)));
        require(arg3 - (address(arg3)));
        require(arg5 - (uint64(arg5)));
        require(arg6 - (bytes1(arg6)));
        address var_a = msg.sender;
        require(!(bytes1(storage_map_b[var_a])), CustomError_756688fe());
        require(!(address(arg1)), CustomError_756688fe());
        require(block.timestamp > (uint64(arg5)), CustomError_756688fe());
        var_a = arg4 >> 0x08;
        require(storage_map_b[var_a] & (0x01 << (bytes1(arg4))), CustomError_756688fe());
        var_a = arg4 >> 0x08;
        storage_map_b[var_a] = storage_map_b[var_a] | (0x01 << (bytes1(arg4)));
        var_a = address(arg0);
        require(!(arg4 < storage_map_b[var_a]), CustomError_8baa579f());
        var_a = var_a;
        require(((var_k + 0x0100) > 0xffffffffffffffff) | ((var_k + 0x0100) < var_k), CustomError_8baa579f());
        uint256 var_k = var_k + 0x0100;
        var_a = var_a;
        var_a = var_a;
        require(((var_k + 0xc0) > 0xffffffffffffffff) | ((var_k + 0xc0) < var_k), CustomError_8baa579f());
        var_k = var_k + 0xc0;
        require(((var_k + 0x80) > 0xffffffffffffffff) | ((var_k + 0x80) < var_k), CustomError_8baa579f());
        var_k = var_k + 0x80;
        require(!(bytes1(arg6) == 0x1b), CustomError_8baa579f());
        require(!(bytes1(arg6) == 0x1b), CustomError_8baa579f());
        require(arg8 > 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0, CustomError_8baa579f());
        require(0, CustomError_8baa579f());
        require(!(0 == (address(arg0))), CustomError_8baa579f());
        require(((var_k + 0x40) > 0xffffffffffffffff) | ((var_k + 0x40) < var_k), CustomError_8baa579f());
        var_k = var_k + 0x40;
        var_a = address(arg1);
        var_b = keccak256(var_a);
        storage_map_b[var_a] = (uint32(storage_map_b[var_a]) | (uint64(var_k.length))) | (address(var_z << 0x40));
        emit Event_3cec0566(address(arg0), address(arg1), uint64(arg2));
        require(!0, CustomError_8baa579f());
        require(!var_b);
        require(arg4 > (arg4 + 0x01), CustomError_f87d9271());
    }
    
    /// @custom:selector    0x78e890ba
    /// @custom:signature   Unresolved_78e890ba() public view returns (uint256)
    function Unresolved_78e890ba() public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0);
        var_b = var_b;
        var_b = var_b;
        if (((var_h + 0xc0) > 0xffffffffffffffff) | ((var_h + 0xc0) < var_h)) {
            return keccak256(var_k);
        }
    }
    
    /// @custom:selector    0x84f4fc6a
    /// @custom:signature   Unresolved_84f4fc6a(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_84f4fc6a(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        var_a = address(arg0);
        storage_map_b[var_a] = 0;
        emit Event_744157cc(msg.sender, address(arg0));
    }
    
    /// @custom:selector    0x7f608253
    /// @custom:signature   Unresolved_7f608253(address arg0, uint256 arg1, bool arg2, uint256 arg3, uint256 arg4) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    function Unresolved_7f608253(address arg0, uint256 arg1, bool arg2, uint256 arg3, uint256 arg4) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg0 - (address(arg0)));
        require(arg2 - (bytes1(arg2)));
        var_b = var_b;
        var_b = var_b;
        require(((var_h + 0xc0) > 0xffffffffffffffff) | ((var_h + 0xc0) < var_h), CustomError_da0700a2());
        uint256 var_h = var_h + 0xc0;
        require(((var_h + 0x80) > 0xffffffffffffffff) | ((var_h + 0x80) < var_h), CustomError_da0700a2());
        require(!(bytes1(arg2) == 0x1b), CustomError_da0700a2());
        require(!(bytes1(arg2) == 0x1b), CustomError_da0700a2());
        require(arg4 > 0x7fffffffffffffffffffffffffffffff5d576e7357a4501ddfe92f46681b20a0, CustomError_da0700a2());
        var_b = 0;
        address var_o = keccak256(var_b);
        require(!(uint64(storage_map_d[var_b])), CustomError_da0700a2());
        require(block.timestamp > (uint64(storage_map_d[var_b])), CustomError_da0700a2());
        return 0;
        require(!var_o);
    }
    
    /// @custom:selector    0x747b8a1c
    /// @custom:signature   Unresolved_747b8a1c(address arg0, uint256 arg1, uint256 arg2) public pure
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_747b8a1c(address arg0, uint256 arg1, uint256 arg2) public pure {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg0 - (address(arg0)));
        require(arg1 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(((var_c + (uint248(0x3f + (arg1 + 0x1f)))) < var_c) | ((var_c + (uint248(0x3f + (arg1 + 0x1f)))) > 0xffffffffffffffff));
        require(arg2 > 0xffffffffffffffff);
    }
    
    /// @custom:selector    0xc1e6613d
    /// @custom:signature   Unresolved_c1e6613d(address arg0, address arg1) public view returns (address)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_c1e6613d(address arg0, address arg1) public view returns (address) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        var_a = address(arg1);
        return address(storage_map_b[var_a] >> 0x40);
    }
    
    /// @custom:selector    0xcf8fbec9
    /// @custom:signature   Unresolved_cf8fbec9(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_cf8fbec9(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        unresolved_97dc97cb = (uint96(unresolved_97dc97cb)) | (address(arg0));
        emit Event_fe60173c(address(arg0));
    }
    
    /// @custom:selector    0x5197a0d3
    /// @custom:signature   Unresolved_5197a0d3(address arg0, uint256 arg1) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_5197a0d3(address arg0, uint256 arg1) public payable {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - arg1);
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        address var_b = address(arg0);
        storage_map_d[var_b] = (bytes1(arg1)) | (uint248(storage_map_d[var_b]));
        emit Event_f09fcf47(address(arg0), arg1);
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
        return storage_map_b[var_a];
    }
    
    /// @custom:selector    0x7ecebe00
    /// @custom:signature   Unresolved_7ecebe00(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_7ecebe00(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_b[var_a];
    }
    
    /// @custom:selector    0x7f6e9d4b
    /// @custom:signature   Unresolved_7f6e9d4b(address arg0) public view returns (bool)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_7f6e9d4b(address arg0) public view returns (bool) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return !(!bytes1(storage_map_b[var_a]));
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
    
    /// @custom:selector    0xb002b9fa
    /// @custom:signature   Unresolved_b002b9fa(address arg0, bool arg1, uint64 arg2) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["bool", "uint8", "bytes1", "int8"]
    /// @param              arg2 ["uint64", "bytes8", "int64"]
    function Unresolved_b002b9fa(address arg0, bool arg1, uint64 arg2) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg2 - (uint64(arg2)));
        require(msg.sender - (address(unresolved_97dc97cb)), CustomError_5c427cd9());
        require(block.timestamp > (uint64(arg2)), CustomError_756688fe());
        var_b = arg1 >> 0x08;
        require(storage_map_d[var_b] & (0x01 << (bytes1(arg1))), CustomError_756688fe());
        var_b = arg1 >> 0x08;
        storage_map_d[var_b] = storage_map_d[var_b] | (0x01 << (bytes1(arg1)));
        var_b = address(arg0);
        require(!(arg1 < storage_map_d[var_b]), CustomError_f87d9271());
        require(arg1 > (arg1 + 0x01), CustomError_f87d9271());
        var_b = address(arg0);
        storage_map_d[var_b] = arg1 + 0x01;
    }
}