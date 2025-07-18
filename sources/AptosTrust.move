module 0xCAFE::AptosTrust {
    use std::signer;
    use std::vector;
    use aptos_framework::big_ordered_map;
    use 0x1::block::{Self, BlockResource};
    use 0x1::aptos_hash;
    use 0x1::ordered_map;
    use 0x1::account;
    use 0x1::event;
    use std::bcs;

    const MODULE_OWNER: address = @0xCAFE;

    const ENOT_MODULE_OWNER: u64 = 1;
    const EVERIFY_HEADER_FAILED: u64 = 2;
    const EINVALID_ROOT_LENGTH: u64 = 3;

    struct ParaChains has key {
        chains: big_ordered_map::BigOrderedMap<u64, bool>
    }

    struct Header has store, copy {
        chainId: u64,
        height: u64,
        relayHeight: u64,
        root: vector<u8>
    }

    struct AllHeaders has key {
        headersByChainId: ordered_map::OrderedMap<u64, vector<u64>>,
        headersByHeight: ordered_map::OrderedMap<vector<u8>, Header>
    }

    struct HCRByHeight has key {
        hcrs: ordered_map::OrderedMap<u64, vector<u8>>
    }

    struct VotesByHeight has key {
        votes: big_ordered_map::BigOrderedMap<u64, u64>
    }

    public entry fun registParaChain(operator: &signer, chainId: u64) acquires ParaChains {
        assert!(signer::address_of(operator) == MODULE_OWNER, ENOT_MODULE_OWNER);
        if (!exists<ParaChains>(MODULE_OWNER)) {
            move_to(operator, ParaChains {chains: big_ordered_map::new<u64, bool>()});
        };
        let chains_mut = &mut borrow_global_mut<ParaChains>(MODULE_OWNER).chains;
        chains_mut.add(chainId, true);
    }

    fun verifyHeader(operator: &signer, chainId: u64, height: u64, root: vector<u8>): bool {
        // TODO add on-chain SPV or zk-SPV
        true
    }

    fun storeHeader(operator: &signer, chainId: u64, height: u64, root: vector<u8>) acquires AllHeaders {
        assert!(signer::address_of(operator) == MODULE_OWNER, ENOT_MODULE_OWNER);
        if (!exists<AllHeaders>(MODULE_OWNER)) {
            move_to(operator, AllHeaders {
                headersByChainId: ordered_map::new<u64, vector<u64>>(),
                headersByHeight: ordered_map::new<vector<u8>, Header>()
            });
        };
        let AllHeaders {headersByChainId, headersByHeight} = borrow_global_mut<AllHeaders>(MODULE_OWNER);
        if (!headersByChainId.contains(&chainId)) {
            headersByChainId.add(chainId, vector::empty<u64>());
        };
        let heights = headersByChainId.borrow_mut(&chainId);
        heights.push_back(height);
        let chainIdBytes = bcs::to_bytes(&chainId);
        let heightBytes = bcs::to_bytes(&height);
        chainIdBytes.append(heightBytes);
        let current_height = block::get_current_block_height();
        headersByHeight.add(chainIdBytes, Header {
            chainId: chainId,
            height: height,
            relayHeight: current_height,
            root: root
        });
    }

    fun build(operator: &signer, chainId: u64, height: u64, root: vector<u8>) acquires HCRByHeight {
        assert!(signer::address_of(operator) == MODULE_OWNER, ENOT_MODULE_OWNER);
        assert!(vector::length(&root) == 32, EINVALID_ROOT_LENGTH);

        if (!exists<HCRByHeight>(MODULE_OWNER)) {
            move_to(operator, HCRByHeight {hcrs: ordered_map::new<u64, vector<u8>>()});
        };

        let hcrs = &mut borrow_global_mut<HCRByHeight>(MODULE_OWNER).hcrs;
        let current_height = block::get_current_block_height();
        if (hcrs.contains(&current_height)) {
            let hcr = hcrs.borrow_mut(&current_height);
            hcr.append(root); // TODO: chainId+height+root
            *hcr = aptos_hash::keccak256(*hcr);
        } else {
            hcrs.add(current_height, root);
        }
    }

    fun countVotes(operator: &signer, sequences: &vector<u64>) acquires VotesByHeight {
        assert!(signer::address_of(operator) == MODULE_OWNER, ENOT_MODULE_OWNER);
        let length = vector::length(sequences);
        if (length == 0) {
            return;
        };
        if (!exists<VotesByHeight>(MODULE_OWNER)) {
            move_to(operator, VotesByHeight { votes: big_ordered_map::new<u64, u64>()});
        };
        let votes = &mut borrow_global_mut<VotesByHeight>(MODULE_OWNER).votes;
        sequences.for_each_ref(|x| {
            if (!votes.contains(x)) {
                votes.add(*x, 0u64);
            };
            let y = votes.borrow_mut(x);
            *y = *y + 1;
        });
    }

    public entry fun collectHeader(operator: &signer, chainId: u64, height: u64, root: vector<u8>, hcr: vector<u8>, sequences: vector<u64>) acquires AllHeaders,VotesByHeight,HCRByHeight {
        // statistic the vote for each history heigtht
        countVotes(operator, &sequences);

        // verify header
        assert!(verifyHeader(operator, chainId, height, root), EVERIFY_HEADER_FAILED);

        // store header
        storeHeader(operator, chainId, height, root);

        // build hcr
        build(operator, chainId, height, root); 
    }

    const CHECK_UNINIT: u64 = 0;
    const CHECK_VOTE_OK: u64 = 1;
    const CHECK_VOTE_NOT_ENOUGH: u64 = 2;
    const CHECK_NOT_EXIST: u64 = 3;
    #[view]
    public fun checkParaHeaderValid(chainId: u64, height: u64) :u64 acquires AllHeaders,VotesByHeight,ParaChains {
        // check whether init AllHeaders
        if (!exists<AllHeaders>(MODULE_OWNER)) {
            return CHECK_UNINIT;
        };

        // calculate key
        let chainIdBytes = bcs::to_bytes(&chainId);
        let heightBytes = bcs::to_bytes(&height);
        chainIdBytes.append(heightBytes);
        
        // get header.relayHeight by key
        let headersByHeight = & borrow_global<AllHeaders>(MODULE_OWNER).headersByHeight;
        if (!headersByHeight.contains(&chainIdBytes)) {
            return CHECK_NOT_EXIST;
        };
        let relayHeight = headersByHeight.borrow(&chainIdBytes).relayHeight;
        
        // get votes of relayHeight
        assert!(exists<VotesByHeight>(MODULE_OWNER));
        let votes = & borrow_global<VotesByHeight>(MODULE_OWNER).votes;
        // assert!(votes.contains(&relayHeight));
        let totalVotes = votes.borrow(&relayHeight);

        // get number of parachains
        assert!(exists<ParaChains>(MODULE_OWNER));
        let totalParachains = borrow_global<ParaChains>(MODULE_OWNER).chains.compute_length();

        // compare
        if (*totalVotes > totalParachains/3*2) {
            return CHECK_VOTE_OK;
        };

        CHECK_VOTE_NOT_ENOUGH       
    }



    // Should be in-sync with NewBlockEvent rust struct in new_block.rs
    #[test_only]
    struct NewBlockEvent has copy, drop, store {
        hash: address,
        epoch: u64,
        round: u64,
        height: u64,
        previous_block_votes_bitvec: vector<u8>,
        proposer: address,
        failed_proposer_indices: vector<u64>,
        /// On-chain time during the block at the given height
        time_microseconds: u64,
    }

    /// Event emitted when a proposal is created.
    #[test_only]
    struct UpdateEpochIntervalEvent has drop, store {
        old_epoch_interval: u64,
        new_epoch_interval: u64,
    }

    #[test(account=@0xCAFE)]
    fun registParaChainByCorrectOwner(account: &signer) acquires ParaChains {
        registParaChain(account, 1u64);
        assert!(borrow_global<ParaChains>(MODULE_OWNER).chains.contains(&1));
        assert!(borrow_global<ParaChains>(MODULE_OWNER).chains.compute_length() == 1);
    }

    #[test(account=@0xCAFF)]
    #[expected_failure]
    fun registParaChainByWrongOwner(account: &signer) acquires ParaChains {
        registParaChain(account, 1u64);
    }

    #[test(account=@0xCAFE, aptos_framework=@aptos_framework)]
    fun storeHeaderOnce(account: &signer, aptos_framework: &signer) acquires AllHeaders{
        aptos_framework::account::create_account_for_test(signer::address_of(aptos_framework));
        block::initialize_for_test(aptos_framework, 3000000u64); // it does not show in doc:reference, but show in codes
        let chainId = 10u64;
        let height = 20u64;
        let root = aptos_hash::keccak256(vector[1u8]);
        storeHeader(account, chainId, height, root);
        let AllHeaders {headersByChainId, headersByHeight} = borrow_global<AllHeaders>(MODULE_OWNER);
        assert!(headersByChainId.length() == 1);
        assert!(headersByHeight.length() == 1);
    }

    #[test(account=@0xCAFE, vm=@vm_reserved, aptos_framework=@aptos_framework)]
    fun buildWithoutPrefix(account: &signer, vm: &signer, aptos_framework: &signer) acquires HCRByHeight {
        aptos_framework::account::create_account_for_test(signer::address_of(aptos_framework));
        block::initialize_for_test(aptos_framework, 3000000u64); // it does not show in doc:reference, but show in codes
        let chainId = 10u64;
        let height = 11u64;
        let root = vector[1u8,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8,1,2,3,4,5,6,7,8];
        build(account, chainId, height, root);
        let current_height = block::get_current_block_height();
        assert!(borrow_global<HCRByHeight>(MODULE_OWNER).hcrs.contains(&current_height));
        assert!(*borrow_global<HCRByHeight>(MODULE_OWNER).hcrs.borrow(&current_height) == root);
    }

    #[test(account=@0xCAFE)]
    fun countVotesNoEmpty(account: &signer) acquires VotesByHeight {
        let sequence = vector[1u64, 2u64, 10u64];
        countVotes(account, &sequence);
        let votes = & borrow_global<VotesByHeight>(MODULE_OWNER).votes;
        assert!(votes.compute_length() == vector::length(&sequence));
    }

    #[test(account=@0xCAFE)]
    fun countVotesEmpty(account: &signer) acquires VotesByHeight {
        let sequence = vector[1u64, 2u64, 10u64];
        countVotes(account, &sequence);
        countVotes(account, &vector[]);
        let votes = & borrow_global<VotesByHeight>(MODULE_OWNER).votes;
        assert!(votes.compute_length() == vector::length(&sequence));
    }

    #[test]
    fun example_with_primitive_types() {
        let map = big_ordered_map::new<u64, u64>();

        map.add(2, 2);
        map.add(3, 3);

        assert!(map.contains(&2));

        let sum = 0;
        map.for_each_ref(|k, v| sum += *k + *v);
        assert!(sum == 10);

        *map.borrow_mut(&2) = 5;
        assert!(map.get(&2).destroy_some() == 5);

        map.for_each_mut(|_k, v| *v += 1);

        let sum = 0;
        map.for_each(|k, v| sum += k + v);
        assert!(sum == 15);
    }

    #[test]
    fun bytesAsKey() {
        let map = ordered_map::new<vector<u8>, u64>();
        let key = vector[1u8,2u8,3u8];
        map.add(key, 3);
        // map.for_each(|k, v| {});
        let key2 = vector[1u8,2u8,3u8];
        assert!(map.contains(&key2));
    }
}