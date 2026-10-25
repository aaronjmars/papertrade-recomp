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
    uint256 public constant unresolved_313ce567 = 18;
    
    bytes32 store_j;
    mapping(bytes32 => bytes32) storage_map_g;
    uint256 store_a;
    address public unresolved_8da5cb5b;
    address public unresolved_12bbf044;
    address public unresolved_07546172;
    uint256 public unresolved_18160ddd;
    bytes32 store_i;
    mapping(bytes32 => bytes32) storage_map_f;
    address public unresolved_ee99205c;
    
    event Event_4ffd725f();
    event Event_6e54fcdf();
    event Event_ddf252ad();
    event Event_ad0f299e();
    event Event_8c5be1e5();
    error CustomError_00000000();
    event Event_6397f5b1();
    
    /// @custom:selector    0x06fdde03
    /// @custom:signature   Unresolved_06fdde03() public view returns (string memory)
    function Unresolved_06fdde03() public view returns (string memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0);
        if (!store_a) {
            if (((store_a >> 0x01) < 0x20) == (store_a)) {
                bytes32 var_c = store_a >> 0x01;
                if (0 == (store_a)) {
                    if (0x01 == (store_a)) {
                        if (0 < (store_a >> 0x01)) {
                            if ((0xa0 < 0x80) | (0xa0 > 0xffffffffffffffff)) {
                                if (0 < var_c) {
                                    return abi.encodePacked(0x20, var_c);
                                    if ((0 < 0x80) | (0 > 0xffffffffffffffff)) {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    /// @custom:selector    0x9dd373b9
    /// @custom:signature   Unresolved_9dd373b9(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_9dd373b9(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        unresolved_ee99205c = (uint96(unresolved_ee99205c)) | (address(arg0));
        emit Event_6397f5b1(address(arg0));
    }
    
    /// @custom:selector    0xa9059cbb
    /// @custom:signature   Unresolved_a9059cbb(address arg0, uint256 arg1) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_a9059cbb(address arg0, uint256 arg1) public payable returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(!(!address(unresolved_ee99205c)), CustomError_e827105e());
        require(address(unresolved_ee99205c) == msg.sender, CustomError_e827105e());
        require(!(address(unresolved_ee99205c) == msg.sender), CustomError_e827105e());
        address var_b = address(msg.sender);
        require(storage_map_f[var_b] < arg1, CustomError_f4d678b8());
        var_b = address(msg.sender);
        if ((storage_map_f[var_b] - arg1) > storage_map_f[var_b]) {
            var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            storage_map_f[var_b] = storage_map_f[var_b] - arg1;
            var_b = address(arg0);
            require((storage_map_f[var_b] - arg1) > storage_map_f[var_b], CustomError_e827105e());
            var_b = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            storage_map_f[var_b] = storage_map_f[var_b] + arg1;
            emit Event_ddf252ad(address(msg.sender), address(arg0), arg1);
            return 0x01;
            require(storage_map_f[var_b] > (storage_map_f[var_b] + arg1), CustomError_e827105e());
        }
        require(!(!address(unresolved_ee99205c)), CustomError_e827105e());
        require(!(address(unresolved_ee99205c)), CustomError_e827105e());
    }
    
    /// @custom:selector    0xd311b1a9
    /// @custom:signature   Unresolved_d311b1a9(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_d311b1a9(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        unresolved_12bbf044 = (uint96(unresolved_12bbf044)) | (address(arg0));
        emit Event_6e54fcdf(address(arg0));
    }
    
    /// @custom:selector    0x23b872dd
    /// @custom:signature   Unresolved_23b872dd(address arg0, address arg1, uint256 arg2) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg2 ["uint256", "bytes32", "int256"]
    function Unresolved_23b872dd(address arg0, address arg1, uint256 arg2) public payable returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x60);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(msg.sender - (address(unresolved_12bbf044)), CustomError_13be252b());
        var_a = msg.sender;
        require(storage_map_g[var_a] < arg2, CustomError_13be252b());
        require((storage_map_g[var_a] - arg2) > storage_map_g[var_a], CustomError_e827105e());
        var_a = msg.sender;
        storage_map_g[var_a] = storage_map_g[var_a] - arg2;
        require(!(!address(unresolved_ee99205c)), CustomError_e827105e());
        require(address(unresolved_ee99205c) == msg.sender, CustomError_e827105e());
        require(!(address(unresolved_ee99205c) == msg.sender), CustomError_e827105e());
        var_a = address(arg0);
        require(storage_map_g[var_a] < arg2, CustomError_f4d678b8());
        var_a = address(arg0);
        if ((storage_map_g[var_a] - arg2) > storage_map_g[var_a]) {
            var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            storage_map_g[var_a] = storage_map_g[var_a] - arg2;
            var_a = address(arg1);
            require((storage_map_g[var_a] - arg2) > storage_map_g[var_a], CustomError_e827105e());
            var_a = 0x4e487b7100000000000000000000000000000000000000000000000000000000;
            storage_map_g[var_a] = storage_map_g[var_a] + arg2;
            emit Event_ddf252ad(address(arg0), address(arg1), arg2);
            return 0x01;
            require(storage_map_g[var_a] > (storage_map_g[var_a] + arg2), CustomError_e827105e());
        }
        require(!(!address(unresolved_ee99205c)), CustomError_e827105e());
        require(!(address(unresolved_ee99205c)), CustomError_e827105e());
    }
    
    /// @custom:selector    0x70a08231
    /// @custom:signature   Unresolved_70a08231(address arg0) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_70a08231(address arg0) public view returns (uint256) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        address var_a = address(arg0);
        return storage_map_g[var_a];
    }
    
    /// @custom:selector    0x95d89b41
    /// @custom:signature   Unresolved_95d89b41() public view returns (string memory)
    function Unresolved_95d89b41() public view returns (string memory) {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0);
        if (!store_i) {
            if (((store_i >> 0x01) < 0x20) == (store_i)) {
                if (!store_i) {
                    if (0x01 == (store_i)) {
                        if (0 < (store_i >> 0x01)) {
                            if (((var_d + (uint248((((var_d + 0) + 0x20) - var_d) + 0x1f))) < var_d) | ((var_d + (uint248((((var_d + 0) + 0x20) - var_d) + 0x1f))) > 0xffffffffffffffff)) {
                                uint248 var_d = var_d + (uint248((((var_d + 0) + 0x20) - var_d) + 0x1f));
                                return abi.encodePacked(0x20, var_d.length);
                                if (((var_d + (uint248((0 - var_d) + 0x1f))) < var_d) | ((var_d + (uint248((0 - var_d) + 0x1f))) > 0xffffffffffffffff)) {
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    /// @custom:selector    0x40c10f19
    /// @custom:signature   Unresolved_40c10f19(address arg0, uint256 arg1) public view
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_40c10f19(address arg0, uint256 arg1) public view {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_07546172)), CustomError_f8d2906c());
        require(unresolved_18160ddd > (unresolved_18160ddd + arg1));
    }
    
    /// @custom:selector    0xdd62ed3e
    /// @custom:signature   Unresolved_dd62ed3e(address arg0, address arg1) public view returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_dd62ed3e(address arg0, address arg1) public view returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(arg1 - (address(arg1)));
        require(address(arg1) == (address(unresolved_12bbf044)));
        var_a = address(arg1);
        return storage_map_g[var_a];
        return 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff;
    }
    
    /// @custom:selector    0x8f15b414
    /// @custom:signature   Unresolved_8f15b414(uint256 arg0, uint256 arg1, address arg2, address arg3) public payable
    /// @param              arg0 ["uint256", "bytes32", "int256"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    /// @param              arg2 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg3 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_8f15b414(uint256 arg0, uint256 arg1, address arg2, address arg3) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x80);
        require(arg0 > 0xffffffffffffffff);
        require(arg0 > 0xffffffffffffffff);
        require(((var_c + (uint248((0x20 + (arg0 + 0x1f)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (arg0 + 0x1f)) + 0x1f))) > 0xffffffffffffffff));
        uint256 var_c = var_c + (uint248((0x20 + (arg0 + 0x1f)) + 0x1f));
        require(arg1 > 0xffffffffffffffff);
        require(arg1 > 0xffffffffffffffff);
        require(((var_c + (uint248((0x20 + (arg1 + 0x1f)) + 0x1f))) < var_c) | ((var_c + (uint248((0x20 + (arg1 + 0x1f)) + 0x1f))) > 0xffffffffffffffff));
        var_c = var_c + (uint248((0x20 + (arg1 + 0x1f)) + 0x1f));
        require(arg2 - (address(arg2)));
        require(arg3 - (address(arg3)));
        if (store_j) {
            require(bytes1(store_j), CustomError_0dc149f0());
            require(!(bytes1(store_j >> 0x08)), CustomError_0dc149f0());
            require(!(bytes1(store_j >> 0x08)), CustomError_0dc149f0());
            require(var_c.length > 0xffffffffffffffff, CustomError_0dc149f0());
            require(!(bytes1(store_a)), CustomError_0dc149f0());
            require(((store_a >> 0x01) < 0x20) == (bytes1(store_a)), CustomError_0dc149f0());
            var_a = 0x01;
            require((store_a >> 0x01) > 0x1f, CustomError_0dc149f0());
            require(var_c.length < 0x20, CustomError_0dc149f0());
            require(keccak256(var_a) + ((var_c.length + 0x1f) >> 0x05) < ((((store_a >> 0x01) + 0x1f) >> 0x05) + keccak256(var_a)), CustomError_0dc149f0());
            var_a = 0x01;
            require(0x01 == (var_c.length > 0x1f), CustomError_0dc149f0());
            require(0 < (uint248(var_c.length)), CustomError_0dc149f0());
            storage_map_g[var_a] = (~(0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff >> (bytes1(var_c.length << 0x03)))) & (var_h);
            store_a = (var_c.length << 0x01) + 0x01;
            require(var_c.length > (uint248(var_c.length)), CustomError_0dc149f0());
            require(var_c.length > 0xffffffffffffffff, CustomError_0dc149f0());
        }
        require(bytes1(store_j), CustomError_0dc149f0());
    }
    
    /// @custom:selector    0x095ea7b3
    /// @custom:signature   Unresolved_095ea7b3(address arg0, uint256 arg1) public payable returns (uint256)
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_095ea7b3(address arg0, uint256 arg1) public payable returns (uint256) {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        var_a = address(arg0);
        storage_map_g[var_a] = arg1;
        emit Event_8c5be1e5(msg.sender, address(arg0), arg1);
        return 0x01;
    }
    
    /// @custom:selector    0x9dc29fac
    /// @custom:signature   Unresolved_9dc29fac(address arg0, uint256 arg1) public view
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    /// @param              arg1 ["uint256", "bytes32", "int256"]
    function Unresolved_9dc29fac(address arg0, uint256 arg1) public view {
        require(msg.value);
        require((msg.data.length + 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc) < 0x40);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_07546172)), CustomError_f8d2906c());
        address var_b = address(arg0);
        require(storage_map_f[var_b] < arg1, CustomError_f4d678b8());
        var_b = address(arg0);
        require((storage_map_f[var_b] - arg1) > storage_map_f[var_b]);
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
    
    /// @custom:selector    0xfca3b5aa
    /// @custom:signature   Unresolved_fca3b5aa(address arg0) public payable
    /// @param              arg0 ["address", "uint160", "bytes20", "int160"]
    function Unresolved_fca3b5aa(address arg0) public payable {
        require(msg.value);
        require((0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffc + msg.data.length) < 0x20);
        require(arg0 - (address(arg0)));
        require(msg.sender - (address(unresolved_8da5cb5b)), CustomError_30cd7471());
        unresolved_07546172 = (address(arg0)) | (uint96(unresolved_07546172));
        emit Event_ad0f299e(address(arg0));
    }
}