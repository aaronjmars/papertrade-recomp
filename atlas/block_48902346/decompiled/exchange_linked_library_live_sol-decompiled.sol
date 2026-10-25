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
    mapping(bytes32 => bytes32) storage_map_g;
    mapping(bytes32 => bytes32) storage_map_a;
    bytes32 store_e;
    mapping(bytes32 => bytes32) storage_map_h;
    bytes32 store_b;
    mapping(bytes32 => bytes32) storage_map_c;
    mapping(bytes32 => bytes32) storage_map_f;
    bytes32 store_d;
    
    error CustomError_00000000();
    event Event_f949f116();
    event Event_4c672bd1();
    
    /// @custom:selector    0xca02ff91
    /// @custom:signature   Unresolved_ca02ff91(uint256 arg0, address arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    function Unresolved_ca02ff91(uint256 arg0, address arg1, uint256 arg2, uint256 arg3) public payable returns (bytes memory) {
        require(0xcd617f984158a4f5d287ddee0e8eb0fed204916d == address(this));
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x80);
        require(arg1 - (address(arg1)));
        if (!address(arg1)) {
            if (arg3) {
                if (arg3 > 0x40) {
                    if (arg2) {
                        if (!arg2) {
                            require(!address(arg1));
                            require(arg3);
                            return abi.encodePacked(0, 0, 0);
                            require(arg3 > 0x40);
                            var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
                            require(!arg2);
                            require(address(storage_map_a[var_a]) == (address(arg1)));
                            require(!(address(storage_map_a[var_a])) == (address(arg1)));
                            emit Event_f949f116(address(arg1), arg2, arg2, 0, 0);
                            return abi.encodePacked(0, 0, arg2);
                            return abi.encodePacked(0, 0, 0);
                            var_a = arg2 + 0x01;
                            require(arg2 > (arg2 + 0x01));
                            require((arg2 + 0x01) < (store_b));
                            storage_map_c[var_a] = (storage_map_c[var_a]) + (storage_map_c[var_a]);
                            storage_map_c[var_a] = 0;
                            require(!0 < 0x40);
                            var_a = storage_map_a[var_a] >> 0xd0;
                            storage_map_a[var_a] = (uint48((storage_map_a[var_a] >> 0xa0) << 0xa0)) | (uint208(storage_map_a[var_a]));
                            require(!0);
                        }
                        require(!storage_map_c[var_a]);
                    }
                    require(address(storage_map_a[var_a]) - (address(arg1)));
                    return abi.encodePacked(0, 0, 0);
                    return abi.encodePacked(0, 0, 0);
                    require(0 == (storage_map_a[var_a] >> 0xd0));
                }
            }
            require(!storage_map_c[var_a]);
        }
        return abi.encodePacked(0, 0, 0);
    }
    
    /// @custom:selector    0xef1a27a9
    /// @custom:signature   Unresolved_ef1a27a9(uint256 arg0, address arg1, address arg2, uint256 arg3, uint256 arg4, uint256 arg5, uint256 arg6, uint256 arg7) public view
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    /// @param              arg6 ["uint256", "bytes32", "int256"]
    /// @param              arg7 ["uint256", "bytes32", "int256"]
    function Unresolved_ef1a27a9(uint256 arg0, address arg1, address arg2, uint256 arg3, uint256 arg4, uint256 arg5, uint256 arg6, uint256 arg7) public view {
        require(0xcd617f984158a4f5d287ddee0e8eb0fed204916d == address(this));
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x0100);
        require(arg1 - (address(arg1)));
        require(arg2 - (address(arg2)));
        require(arg4 - arg4);
        if (0 == (arg3 > 0)) {
            if (!(((arg3 * arg5) / arg3) == arg5) | !arg3) {
                if (!arg4) {
                    if (address(arg2) > (address(arg2) + arg3)) {
                        if (arg3 > 0) {
                            if ((address(arg2) + arg3) - ((arg3 * arg5) / 0x0de0b6b3a7640000) > (address(arg2) + arg3)) {
                                if (!store_d) {
                                    if (!store_d) {
                                        require(0 == (arg3 > 0));
                                        require(!(((arg3 * arg5) / arg3) == arg5) | !arg3);
                                    }
                                    require(!arg4);
                                    require(address(arg2) > (address(arg2) + arg3));
                                    require(arg3 > 0);
                                }
                            }
                        }
                    }
                }
            }
            require((address(arg2) + arg3) - ((arg3 * arg5) / 0x0de0b6b3a7640000) > (address(arg2) + arg3));
            require(arg3 == 0x8000000000000000000000000000000000000000000000000000000000000000);
        }
    }
    
    /// @custom:selector    0x3f4e3626
    /// @custom:signature   Unresolved_3f4e3626(uint256 arg0, address arg1, uint256 arg2) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_3f4e3626(uint256 arg0, address arg1, uint256 arg2) public payable {
        require(0xcd617f984158a4f5d287ddee0e8eb0fed204916d == address(this));
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg1 - (address(arg1)));
        if (arg2) {
            require(arg2);
            var_a = storage_map_a[var_a];
            require(!storage_map_a[var_a]);
            require(0 == (!(storage_map_c[var_a]) > arg2));
            var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            storage_map_c[var_a] = 0;
            var_a = storage_map_a[var_a];
            require((storage_map_c[var_a] - arg2) > (storage_map_c[var_a]));
            var_a = storage_map_a[var_a] >> 0xd0;
            storage_map_a[var_a] = (uint48((storage_map_a[var_a] >> 0xa0) << 0xa0)) | (uint208(storage_map_a[var_a]));
            require(0 == (storage_map_a[var_a] >> 0xd0));
        }
        store_d = store_d;
        var_a = address(arg1);
        storage_map_a[var_a] = storage_map_a[var_a];
        require(!store_d);
        emit Event_4c672bd1(address(arg1), arg2);
        store_e = store_b;
        emit Event_4c672bd1(address(arg1), arg2);
    }
    
    /// @custom:selector    0x18958ce2
    /// @custom:signature   Unresolved_18958ce2(uint256 arg0, address arg1, uint256 arg2) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_18958ce2(uint256 arg0, address arg1, uint256 arg2) public payable {
        require(0xcd617f984158a4f5d287ddee0e8eb0fed204916d == address(this));
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg1 - (address(arg1)));
        require(!arg2, CustomError_ea097be6());
        store_b = (store_b) + 0x01;
        require(store_b > 0xffffffffffff, CustomError_ea097be6());
        require(((var_d + 0x80) < var_d) | ((var_d + 0x80) > 0xffffffffffffffff));
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        uint256 var_d = var_d + 0x80;
        var_b = store_b;
        storage_map_f[var_b] = (uint96(storage_map_f[var_b])) | (address(var_d.length));
        storage_map_f[var_b] = (uint48(var_i << 0xa0)) | (uint208(storage_map_f[var_b]));
        storage_map_f[var_b] = (uint48(var_j << 0xd0)) | (uint208(storage_map_f[var_b]));
        storage_map_g[var_b] = var_k;
        require(!store_e);
        require(!storage_map_f[var_b]);
        var_b = storage_map_f[var_b];
        storage_map_f[var_b] = (uint48(store_b << 0xa0)) | (uint208(storage_map_f[var_b]));
        var_b = address(arg1);
        storage_map_f[var_b] = store_b;
        require(store_d > (store_d + arg2));
    }
    
    /// @custom:selector    0x32db40c9
    /// @custom:signature   Unresolved_32db40c9(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    function Unresolved_32db40c9(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory) {
        require(0xcd617f984158a4f5d287ddee0e8eb0fed204916d == address(this));
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg1 - (address(arg1)));
        require(!(!address(arg1)), CustomError_5b6d2b7a());
        require(arg2, CustomError_5b6d2b7a());
        require(!(!arg3 > arg2), CustomError_5b6d2b7a());
        require(!(arg3 < (store_b)), CustomError_5b6d2b7a());
        require(arg4, CustomError_5b6d2b7a());
        require(arg4 > 0x40, CustomError_5b6d2b7a());
        require((arg3 - arg2) > arg3, CustomError_5b6d2b7a());
        require((arg3 - arg2) > 0x40, CustomError_5b6d2b7a());
        uint256 var_a = arg2;
        require(address(storage_map_a[var_a]) == (address(arg1)), CustomError_5b6d2b7a());
        require(!(address(storage_map_a[var_a]) == (address(arg1))), CustomError_5b6d2b7a());
        require(arg2 > (arg2 + 0x01), CustomError_5b6d2b7a());
        require(!((arg2 + 0x01) > arg3), CustomError_5b6d2b7a());
        var_a = arg2 + 0x01;
        require(storage_map_c[var_a], CustomError_5b6d2b7a());
        require(address(storage_map_a[var_a]) - (address(arg1)), CustomError_5b6d2b7a());
        storage_map_c[var_a] = (storage_map_c[var_a]) + (storage_map_c[var_a]);
        storage_map_c[var_a] = 0;
        var_a = arg2 + 0x01;
        if (0 == (storage_map_a[var_a] >> 0xd0)) {
            var_a = storage_map_a[var_a] >> 0xd0;
            storage_map_a[var_a] = (uint48((storage_map_a[var_a] >> 0xa0) << 0xa0)) | (uint208(storage_map_a[var_a]));
            require(0 == (storage_map_a[var_a] >> 0xd0), CustomError_5b6d2b7a());
        }
        require(0, CustomError_5b6d2b7a());
        var_a = var_a;
        emit Event_f949f116(address(arg1), arg2, arg2, 0, 0);
        return abi.encodePacked(0, 0, arg2);
        return abi.encodePacked(0, 0, 0);
        require(!(storage_map_c[var_a]), CustomError_5b6d2b7a());
        if ((arg3 - arg2) > arg3) {
            require((arg3 - arg2) > arg3, CustomError_5b6d2b7a());
        }
    }
    
    /// @custom:selector    0x79810ffe
    /// @custom:signature   Unresolved_79810ffe(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    function Unresolved_79810ffe(uint256 arg0, uint256 arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory) {
        require(0xcd617f984158a4f5d287ddee0e8eb0fed204916d == address(this));
        if ((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0) {
            require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
            require(store_e < (store_b));
            require(arg2);
            uint256 var_a = store_e;
            require(!0 < arg1);
            require(!storage_map_c[var_a]);
            var_a = var_a;
            require(arg2 < (storage_map_c[var_a]));
            var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            storage_map_c[var_a] = (storage_map_c[var_a]) - arg2;
            var_a = address(storage_map_a[var_a]);
            require((storage_map_c[var_a] - arg2) > (storage_map_c[var_a]));
            var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            storage_map_c[var_a] = 0;
            var_a = store_e;
            require(storage_map_a[var_a] > (storage_map_a[var_a] + arg2));
            var_a = storage_map_a[var_a] >> 0xd0;
            storage_map_a[var_a] = (uint48((storage_map_a[var_a] >> 0xa0) << 0xa0)) | (uint208(storage_map_a[var_a]));
            require(0 == (storage_map_a[var_a] >> 0xd0));
        }
        require(0 == (!store_d));
        store_e = store_e;
        store_d = store_d;
        return abi.encodePacked(0, arg4);
        store_e = store_b;
        store_d = store_d;
        return abi.encodePacked(0, arg4);
    }
    
    /// @custom:selector    0x2448a553
    /// @custom:signature   Unresolved_2448a553(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    function Unresolved_2448a553(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4) public payable returns (bytes memory) {
        require(0xcd617f984158a4f5d287ddee0e8eb0fed204916d == address(this));
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xa0);
        require(arg1 - (address(arg1)));
        if (address(arg1)) {
            if (!arg4) {
                if (arg3) {
                    if (arg3 > 0x40) {
                        if (arg2) {
                            if (!arg2) {
                                uint256 var_a = arg2;
                                if (address(storage_map_a[var_a]) == (address(arg1))) {
                                    if (address(storage_map_a[var_a]) == (address(arg1))) {
                                        if (!(address(storage_map_a[var_a])) == (address(arg1))) {
                                            return abi.encodePacked(0, 0, 0);
                                            if (arg2) {
                                                require(address(arg1));
                                                require(!arg4);
                                                require(arg3);
                                                require(arg3 > 0x40);
                                                require(!arg2);
                                                var_a = arg2;
                                                storage_map_c[var_a] = 0;
                                                var_a = arg2;
                                                require(address(storage_map_a[var_a]) == (address(arg1)));
                                                var_a = storage_map_a[var_a] >> 0xd0;
                                                storage_map_a[var_a] = (uint48((storage_map_a[var_a] >> 0xa0) << 0xa0)) | (uint208(storage_map_a[var_a]));
                                                require(address(storage_map_a[var_a]) == (address(arg1)));
                                            }
                                            var_a = 0;
                                            require(!(address(storage_map_a[var_a])) == (address(arg1)));
                                            var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
                                            storage_map_c[var_a] = (storage_map_c[var_a]) + 0;
                                            emit Event_f949f116(address(arg1), arg2, 0, 0, 0);
                                            return abi.encodePacked(0, 0, 0);
                                            return abi.encodePacked(0, 0, 0);
                                            require(arg2);
                                            require(!0 < 0x40);
                                            require(0);
                                            require(0);
                                            var_a = uint48(storage_map_a[var_a] >> 0xa0);
                                            require(!0);
                                            require(0 < 0);
                                            require(0 == (storage_map_a[var_a] >> 0xd0));
                                            var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
                                            require(storage_map_c[var_a] > (storage_map_c[var_a] + 0));
                                        }
                                        require(address(arg1) == (address(storage_map_a[var_a])));
                                    }
                                    require(address(arg1) == (address(storage_map_a[var_a])));
                                }
                                require(!(address(arg1)) == (address(storage_map_a[var_a])));
                            }
                            require(!uint48(storage_map_a[var_a] >> 0xa0));
                        }
                        require(address(storage_map_a[var_a]) == (address(arg1)));
                        return abi.encodePacked(0, 0, 0);
                        require(!(address(storage_map_a[var_a])) == (address(arg1)));
                    }
                    return abi.encodePacked(0, 0, 0);
                    require(storage_map_c[var_a] > (storage_map_c[var_a] + (0 + (storage_map_c[var_a]))));
                }
            }
            require(!(storage_map_h[var_a]) < arg4);
        }
        return abi.encodePacked(0, 0, 0);
    }
    
    /// @custom:selector    0x82296364
    /// @custom:signature   Unresolved_82296364(uint64 arg0, uint64 arg1, address arg2, uint32 arg3, uint256 arg4) public pure
    /// @param              arg0 ["uint64", "bytes8", "int64"]
    /// @param              arg1 ["uint64", "bytes8", "int64"]
    /// @param              arg2 ["address", "uint128", "bytes16", "int128"]
    /// @param              arg3 ["uint32", "bytes4", "int32"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    function Unresolved_82296364(uint64 arg0, uint64 arg1, address arg2, uint32 arg3, uint256 arg4) public pure {
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x0120);
        require(arg0 - (uint64(arg0)));
        require(arg1 - (uint64(arg1)));
        require(arg2 - (address(arg2)));
        require(arg3 - (uint32(arg3)));
        require(arg4 - arg4);
        if (0 == arg4) {
            if (uint64(arg0) + (uint64(arg0 / 0xc350)) > 0xffffffffffffffff) {
                if (!(uint64(arg1)) > (uint64(arg0 + (arg0 / 0xc350)))) {
                    if (uint64(arg1) - (uint64(arg0 / 0xc350)) > 0xffffffffffffffff) {
                        require(0 == arg4);
                        require(uint64(arg0) + (uint64(arg0 / 0xc350)) > 0xffffffffffffffff);
                        require(!(uint64(arg1)) > (uint64(arg0 + (arg0 / 0xc350))));
                        require(uint64(arg1) - (uint64(arg0 / 0xc350)) > 0xffffffffffffffff);
                        require(uint64(arg1 - (arg0 / 0xc350)) - (uint64(arg0)) < (uint64(arg1 - (arg0 / 0xc350))) & (0 > (uint64(arg0))) | (uint64(arg1 - (arg0 / 0xc350)) - (uint64(arg0)) > (uint64(arg1 - (arg0 / 0xc350))) & (!0 > (uint64(arg0)))));
                        require((uint32(arg3) == 0x8000000000000000000000000000000000000000000000000000000000000000) & (address(arg2) < 0));
                    }
                    require(!(!address(arg2)) | (address(arg2) * (uint32(arg3)) / (address(arg2)) == (uint32(arg3))));
                }
            }
            require(uint64(arg1) > (uint64(arg0)));
            require(uint64(arg1) + (uint64(arg0 / 0xc350)) > 0xffffffffffffffff);
            require(!(uint64(arg1 + (arg0 / 0xc350))) < (uint64(arg0)));
        }
    }
    
    /// @custom:selector    0x3cf4208d
    /// @custom:signature   Unresolved_3cf4208d(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public payable returns (bytes memory)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    function Unresolved_3cf4208d(uint256 arg0, address arg1, uint256 arg2, uint256 arg3, uint256 arg4, uint256 arg5) public payable returns (bytes memory) {
        require(0xcd617f984158a4f5d287ddee0e8eb0fed204916d == address(this));
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xc0);
        require(arg1 - (address(arg1)));
        require(!(!address(arg1)), CustomError_5b6d2b7a());
        require(arg5, CustomError_5b6d2b7a());
        require(arg2, CustomError_5b6d2b7a());
        require(!arg3, CustomError_5b6d2b7a());
        require(arg2 == arg3, CustomError_5b6d2b7a());
        require(arg4, CustomError_5b6d2b7a());
        require(arg4 > 0x40, CustomError_5b6d2b7a());
        require(!(arg2 == arg3), CustomError_5b6d2b7a());
        require(!(0 < 0x40), CustomError_5b6d2b7a());
        require(arg2 == arg3, CustomError_5b6d2b7a());
        require(!(!arg2 == arg3), CustomError_5b6d2b7a());
        require(!(arg2 == arg3), CustomError_5b6d2b7a());
        uint256 var_b = arg3;
        require(address(storage_map_f[var_b]) == (address(arg1)), CustomError_5b6d2b7a());
        require(!(address(storage_map_f[var_b]) == (address(arg1))), CustomError_5b6d2b7a());
        if (0 < 0) {
            var_b = var_b;
            storage_map_g[var_b] = 0;
            require(0 < 0, CustomError_5b6d2b7a());
            var_b = storage_map_f[var_b] >> 0xd0;
            storage_map_f[var_b] = (uint48((storage_map_f[var_b] >> 0xa0) << 0xa0)) | (uint208(storage_map_f[var_b]));
            require(0 == (storage_map_f[var_b] >> 0xd0), CustomError_5b6d2b7a());
        }
        var_b = arg3;
        require(storage_map_g[var_b] > (storage_map_g[var_b] + 0), CustomError_5b6d2b7a());
        var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
        storage_map_g[var_b] = (storage_map_g[var_b]) + 0;
        var_b = var_b;
        emit Event_f949f116(address(arg1), arg2, arg3, 0, 0);
        return abi.encodePacked(0, 0, arg3);
        require(!(storage_map_g[var_b]), CustomError_5b6d2b7a());
        require(!0, CustomError_5b6d2b7a());
        if (0) {
        }
        var_b = arg2;
        require(address(storage_map_f[var_b]) == (address(arg1)), CustomError_5b6d2b7a());
        require(!(!(address(storage_map_f[var_b])) == (address(arg1))), CustomError_5b6d2b7a());
        require(!(address(storage_map_f[var_b]) == (address(arg1))), CustomError_5b6d2b7a());
        require(!(uint48(storage_map_f[var_b] >> 0xa0)), CustomError_5b6d2b7a());
        require(!(storage_map_g[var_b] < arg5), CustomError_5b6d2b7a());
        if (storage_map_g[var_b]) {
        }
        if (arg2 == arg3) {
        }
        if (!arg4) {
        }
    }
    
    /// @custom:selector    0xb67f3dd7
    /// @custom:signature   Unresolved_b67f3dd7(uint256 arg0, uint64 arg1, uint64 arg2, uint256 arg3, uint256 arg4, uint256 arg5, uint256 arg6) public pure returns (uint256)
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint64", "bytes8", "int64"]
    /// @param              arg2 ["uint64", "bytes8", "int64"]
    /// @param              arg3 ["uint256", "bytes32", "int256"]
    /// @param              arg4 ["uint256", "bytes32", "int256"]
    /// @param              arg5 ["uint256", "bytes32", "int256"]
    /// @param              arg6 ["uint256", "bytes32", "int256"]
    function Unresolved_b67f3dd7(uint256 arg0, uint64 arg1, uint64 arg2, uint256 arg3, uint256 arg4, uint256 arg5, uint256 arg6) public pure returns (uint256) {
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0xe0);
        require(arg1 - (uint64(arg1)));
        require(arg2 - (uint64(arg2)));
        require(!(uint64(arg1)) < (uint64(arg2)));
        require(uint64(arg2) - (uint64(arg1)) > 0xffffffffffffffff);
        require(!uint64(arg2 - (arg1)));
        require(0x0de0b6b3a7640000 - ((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg2 - (arg1)))));
        require(!uint64(arg1));
        require(!(((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1)) * arg4) / ((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1))) == arg4) | (!(uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1))));
        require(!((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1)) * arg4) / 0x0de0b6b3a7640000);
        require(!((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1)) * arg4) / 0x0de0b6b3a7640000);
        require(((0x0f4240 * ((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1)))) / 0x0f4240) - ((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1))));
        require(((0x0f4240 * ((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1)))) / 0x0f4240) - ((uint64(arg2 - (arg1)) * 0x0de0b6b3a7640000) / (uint64(arg1))));
        return 0;
    }
}