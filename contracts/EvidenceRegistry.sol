// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract EvidenceRegistry {
    struct Evidence {
        bytes32 evidenceHash;
        uint256 timestamp;
        address submitter;
    }

    uint256 public recordCount;
    mapping(uint256 => Evidence) private records;

    event EvidenceRegistered(
        uint256 indexed recordId,
        bytes32 indexed evidenceHash,
        uint256 timestamp,
        address indexed submitter
    );

    function registerEvidence(bytes32 _evidenceHash) external returns (uint256 recordId) {
        recordId = recordCount++;

        records[recordId] = Evidence({
            evidenceHash: _evidenceHash,
            timestamp: block.timestamp,
            submitter: msg.sender
        });

        emit EvidenceRegistered(
            recordId,
            _evidenceHash,
            block.timestamp,
            msg.sender
        );
    }

    function getEvidence(uint256 recordId)
        external
        view
        returns (
            bytes32 evidenceHash,
            uint256 timestamp,
            address submitter
        )
    {
        require(recordId < recordCount, "Record does not exist");
        Evidence memory e = records[recordId];
        return (e.evidenceHash, e.timestamp, e.submitter);
    }
}
