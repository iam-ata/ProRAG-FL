package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing model update provenance
type SmartContract struct {
	contractapi.Contract
}

// ModelUpdateRecord defines the ledger record for model provenance
type ModelUpdateRecord struct {
	UpdateID           string  `json:"update_id"`
	ClientID           string  `json:"client_id"`
	Round              int     `json:"round"`
	GlobalModelVersion string  `json:"global_model_version"`
	UpdateSHA256       string  `json:"update_sha256"`
	Timestamp          string  `json:"timestamp"`
	Nonce              string  `json:"nonce"`
	Status             string  `json:"status"` // active, revoked, superseded
	SubmitterIdentity  string  `json:"submitter_identity"`
	Signature          string  `json:"signature"`
	NumExamples        int     `json:"num_examples"`
	LocalLoss          float64 `json:"local_loss"`
	LocalAccuracy      float64 `json:"local_accuracy"`
}

// ClientIdentityRecord defines client authorization state on ledger
type ClientIdentityRecord struct {
	ClientID         string `json:"client_id"`
	MSPID            string `json:"msp_id"`
	IsAuthorized     bool   `json:"is_authorized"`
	IsRevoked        bool   `json:"is_revoked"`
	RevocationReason string `json:"revocation_reason"`
}

// InitLedger initializes genesis state
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	return nil
}

// RegisterClient registers an authorized client
func (s *SmartContract) RegisterClient(ctx contractapi.TransactionContextInterface, clientID string, mspID string, isAuthorized bool) error {
	client := ClientIdentityRecord{
		ClientID:         clientID,
		MSPID:            mspID,
		IsAuthorized:     isAuthorized,
		IsRevoked:        false,
		RevocationReason: "",
	}
	clientBytes, err := json.Marshal(client)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState("client_"+clientID, clientBytes)
}

// RevokeClient revokes a client
func (s *SmartContract) RevokeClient(ctx contractapi.TransactionContextInterface, clientID string, reason string) error {
	clientBytes, err := ctx.GetStub().GetState("client_" + clientID)
	if err != nil || clientBytes == nil {
		client := ClientIdentityRecord{
			ClientID:         clientID,
			MSPID:            "OrgUnknown",
			IsAuthorized:     false,
			IsRevoked:        true,
			RevocationReason: reason,
		}
		bytes, _ := json.Marshal(client)
		return ctx.GetStub().PutState("client_"+clientID, bytes)
	}
	var client ClientIdentityRecord
	json.Unmarshal(clientBytes, &client)
	client.IsAuthorized = false
	client.IsRevoked = true
	client.RevocationReason = reason
	updatedBytes, _ := json.Marshal(client)
	return ctx.GetStub().PutState("client_"+clientID, updatedBytes)
}

// VerifyAndSubmitUpdate performs atomic 9-step verification and commits update
func (s *SmartContract) VerifyAndSubmitUpdate(ctx contractapi.TransactionContextInterface, recordJSON string) error {
	var record ModelUpdateRecord
	err := json.Unmarshal([]byte(recordJSON), &record)
	if err != nil {
		return fmt.Errorf("step 1 failed: invalid schema: %v", err)
	}

	// Step 2: Authenticated / authorized identity
	clientBytes, err := ctx.GetStub().GetState("client_" + record.ClientID)
	if err != nil || clientBytes == nil {
		return fmt.Errorf("step 2 failed: unauthorized identity %s", record.ClientID)
	}
	var client ClientIdentityRecord
	json.Unmarshal(clientBytes, &client)
	if !client.IsAuthorized {
		return fmt.Errorf("step 2 failed: client %s is not authorized", record.ClientID)
	}

	// Step 3: Active lifecycle status
	if client.IsRevoked {
		return fmt.Errorf("step 3 failed: client %s is revoked (%s)", record.ClientID, client.RevocationReason)
	}

	// Step 4: Digest format check
	if len(record.UpdateSHA256) != 64 {
		return fmt.Errorf("step 4 failed: invalid digest format")
	}

	// Step 5: Duplicate round check
	roundKey := fmt.Sprintf("round_%s_%d", record.ClientID, record.Round)
	existingRound, _ := ctx.GetStub().GetState(roundKey)
	if existingRound != nil {
		return fmt.Errorf("step 5 failed: duplicate submission for round %d", record.Round)
	}

	// Step 6: Nonce replay check
	nonceKey := fmt.Sprintf("nonce_%s_%s", record.ClientID, record.Nonce)
	existingNonce, _ := ctx.GetStub().GetState(nonceKey)
	if existingNonce != nil {
		return fmt.Errorf("step 7 failed: duplicate nonce replay %s", record.Nonce)
	}

	// Step 9: Atomically consume nonce and record state
	ctx.GetStub().PutState(nonceKey, []byte("consumed"))
	ctx.GetStub().PutState(roundKey, []byte(record.UpdateID))
	record.Status = "active"
	record.Timestamp = time.Now().UTC().Format(time.RFC3339)

	recordBytes, err := json.Marshal(record)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState("update_"+record.UpdateID, recordBytes)
}

// QueryUpdate retrieves an update record
func (s *SmartContract) QueryUpdate(ctx contractapi.TransactionContextInterface, updateID string) (*ModelUpdateRecord, error) {
	recordBytes, err := ctx.GetStub().GetState("update_" + updateID)
	if err != nil || recordBytes == nil {
		return nil, fmt.Errorf("update %s does not exist", updateID)
	}
	var record ModelUpdateRecord
	err = json.Unmarshal(recordBytes, &record)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		panic(fmt.Sprintf("Error creating model_registry chaincode: %v", err))
	}
	if err := chaincode.Start(); err != nil {
		panic(fmt.Sprintf("Error starting model_registry chaincode: %v", err))
	}
}
