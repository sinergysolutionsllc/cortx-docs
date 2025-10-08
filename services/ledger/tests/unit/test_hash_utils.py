"""
Unit tests for hash utilities
"""



from app.hash_utils import GENESIS_HASH, compute_chain_hash, compute_content_hash, sha256_hex


class TestSHA256Hex:
    """Tests for sha256_hex function"""

    def test_hash_string(self):
        """Test hashing a simple string"""
        result = sha256_hex("hello world")
        assert isinstance(result, str)
        assert len(result) == 64
        # SHA-256 of "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert result == expected

    def test_hash_empty_string(self):
        """Test hashing an empty string"""
        result = sha256_hex("")
        assert isinstance(result, str)
        assert len(result) == 64
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result == expected

    def test_hash_bytes(self):
        """Test hashing bytes"""
        result = sha256_hex(b"hello world")
        assert isinstance(result, str)
        assert len(result) == 64
        # Should be the same as string
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert result == expected

    def test_hash_dict(self):
        """Test hashing a dictionary"""
        data = {"key": "value", "number": 42}
        result = sha256_hex(data)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_dict_consistent(self):
        """Test that dict hashing is consistent regardless of key order"""
        data1 = {"key": "value", "number": 42}
        data2 = {"number": 42, "key": "value"}

        result1 = sha256_hex(data1)
        result2 = sha256_hex(data2)

        # Should be the same due to sort_keys=True
        assert result1 == result2

    def test_hash_nested_dict(self):
        """Test hashing nested dictionary"""
        data = {
            "outer": {
                "inner": "value",
                "list": [1, 2, 3],
            },
            "number": 42,
        }
        result = sha256_hex(data)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_list(self):
        """Test hashing a list"""
        data = [1, 2, 3, 4, 5]
        result = sha256_hex(data)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_different_inputs_different_hashes(self):
        """Test that different inputs produce different hashes"""
        hash1 = sha256_hex("hello")
        hash2 = sha256_hex("world")
        assert hash1 != hash2

    def test_same_input_same_hash(self):
        """Test that same input produces same hash (deterministic)"""
        data = {"key": "value", "number": 42}
        hash1 = sha256_hex(data)
        hash2 = sha256_hex(data)
        assert hash1 == hash2

    def test_hash_with_special_characters(self):
        """Test hashing string with special characters"""
        data = {"special": "!@#$%^&*()_+-=[]{}|;':\",./<>?"}
        result = sha256_hex(data)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_with_unicode(self):
        """Test hashing string with unicode characters"""
        data = {"unicode": "こんにちは世界 🌍"}
        result = sha256_hex(data)
        assert isinstance(result, str)
        assert len(result) == 64


class TestComputeContentHash:
    """Tests for compute_content_hash function"""

    def test_compute_content_hash_simple(self):
        """Test computing content hash for simple event data"""
        event_data = {"action": "test", "value": 123}
        result = compute_content_hash(event_data)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_compute_content_hash_empty(self):
        """Test computing content hash for empty event data"""
        event_data = {}
        result = compute_content_hash(event_data)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_compute_content_hash_complex(self):
        """Test computing content hash for complex event data"""
        event_data = {
            "document_id": "doc-123",
            "file_name": "test.pdf",
            "file_size": 1024,
            "metadata": {
                "author": "John Doe",
                "tags": ["test", "pdf", "document"],
            },
        }
        result = compute_content_hash(event_data)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_compute_content_hash_deterministic(self):
        """Test that content hash is deterministic"""
        event_data = {"action": "test", "value": 123}
        hash1 = compute_content_hash(event_data)
        hash2 = compute_content_hash(event_data)
        assert hash1 == hash2

    def test_compute_content_hash_key_order_independent(self):
        """Test that key order doesn't affect hash"""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "b": 2, "a": 1}
        hash1 = compute_content_hash(data1)
        hash2 = compute_content_hash(data2)
        assert hash1 == hash2

    def test_compute_content_hash_different_data(self):
        """Test that different data produces different hashes"""
        data1 = {"action": "test1"}
        data2 = {"action": "test2"}
        hash1 = compute_content_hash(data1)
        hash2 = compute_content_hash(data2)
        assert hash1 != hash2

    def test_compute_content_hash_with_null_values(self):
        """Test computing hash with null values"""
        event_data = {"action": "test", "value": None}
        result = compute_content_hash(event_data)
        assert isinstance(result, str)
        assert len(result) == 64


class TestComputeChainHash:
    """Tests for compute_chain_hash function"""

    def test_compute_chain_hash(self):
        """Test computing chain hash from content and previous hashes"""
        content_hash = "a" * 64
        previous_hash = "b" * 64
        result = compute_chain_hash(content_hash, previous_hash)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_compute_chain_hash_with_genesis(self):
        """Test computing chain hash with genesis hash as previous"""
        content_hash = "a" * 64
        result = compute_chain_hash(content_hash, GENESIS_HASH)
        assert isinstance(result, str)
        assert len(result) == 64

    def test_compute_chain_hash_deterministic(self):
        """Test that chain hash is deterministic"""
        content_hash = "a" * 64
        previous_hash = "b" * 64
        hash1 = compute_chain_hash(content_hash, previous_hash)
        hash2 = compute_chain_hash(content_hash, previous_hash)
        assert hash1 == hash2

    def test_compute_chain_hash_different_content(self):
        """Test that different content produces different chain hash"""
        previous_hash = "b" * 64
        hash1 = compute_chain_hash("a" * 64, previous_hash)
        hash2 = compute_chain_hash("c" * 64, previous_hash)
        assert hash1 != hash2

    def test_compute_chain_hash_different_previous(self):
        """Test that different previous hash produces different chain hash"""
        content_hash = "a" * 64
        hash1 = compute_chain_hash(content_hash, "b" * 64)
        hash2 = compute_chain_hash(content_hash, "c" * 64)
        assert hash1 != hash2

    def test_compute_chain_hash_order_matters(self):
        """Test that order of hashes matters (not commutative)"""
        hash_a = "a" * 64
        hash_b = "b" * 64
        result1 = compute_chain_hash(hash_a, hash_b)
        result2 = compute_chain_hash(hash_b, hash_a)
        assert result1 != result2


class TestGenesisHash:
    """Tests for GENESIS_HASH constant"""

    def test_genesis_hash_format(self):
        """Test that genesis hash is correctly formatted"""
        assert isinstance(GENESIS_HASH, str)
        assert len(GENESIS_HASH) == 64
        assert GENESIS_HASH == "0" * 64

    def test_genesis_hash_all_zeros(self):
        """Test that genesis hash is all zeros"""
        assert all(c == "0" for c in GENESIS_HASH)


class TestHashChainIntegrity:
    """Integration tests for hash chain integrity"""

    def test_simple_chain(self):
        """Test creating a simple hash chain"""
        # Event 1 (genesis)
        data1 = {"action": "event1"}
        content1 = compute_content_hash(data1)
        chain1 = compute_chain_hash(content1, GENESIS_HASH)

        # Event 2
        data2 = {"action": "event2"}
        content2 = compute_content_hash(data2)
        chain2 = compute_chain_hash(content2, chain1)

        # Event 3
        data3 = {"action": "event3"}
        content3 = compute_content_hash(data3)
        chain3 = compute_chain_hash(content3, chain2)

        # All chain hashes should be different
        assert chain1 != chain2
        assert chain2 != chain3
        assert chain1 != chain3

        # All chain hashes should be valid format
        for chain_hash in [chain1, chain2, chain3]:
            assert isinstance(chain_hash, str)
            assert len(chain_hash) == 64

    def test_tampering_detection(self):
        """Test that tampering can be detected"""
        # Original chain
        data1 = {"action": "event1", "value": 100}
        content1 = compute_content_hash(data1)
        chain1 = compute_chain_hash(content1, GENESIS_HASH)

        # Tampered data
        tampered_data = {"action": "event1", "value": 999}
        tampered_content = compute_content_hash(tampered_data)

        # Tampered content hash should be different
        assert content1 != tampered_content

        # If we recalculate the chain hash with tampered content
        tampered_chain = compute_chain_hash(tampered_content, GENESIS_HASH)

        # It should be different from the original
        assert chain1 != tampered_chain

    def test_chain_recomputation(self):
        """Test that chain can be recomputed to verify integrity"""
        events = [
            {"action": "event1", "value": 1},
            {"action": "event2", "value": 2},
            {"action": "event3", "value": 3},
        ]

        # Build chain
        chain_hashes = []
        previous = GENESIS_HASH

        for event_data in events:
            content = compute_content_hash(event_data)
            chain = compute_chain_hash(content, previous)
            chain_hashes.append(chain)
            previous = chain

        # Verify chain by recomputing
        previous = GENESIS_HASH
        for i, event_data in enumerate(events):
            content = compute_content_hash(event_data)
            chain = compute_chain_hash(content, previous)
            # Should match the stored chain hash
            assert chain == chain_hashes[i]
            previous = chain
