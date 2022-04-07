pragma solidity ^0.4.19;

contract Test {
    // address Owner;
    // address adr;
    // uint256 public Limit= 1000000000000000000;
    // address emails = 0x25df6e3da49f41ef5b99e139c87abc12c3583d13;

    function main(uint256 x) external returns(uint256){
      if (x > 5){
        return this.multiply(x);
      }
    }

    function multiply(uint256 x) public returns(uint256){
      return x * 10;
    }

    // function add3(uint256 x) public returns(uint256){
    //   return x + 3;
    // }
    
    // function withdrawal()
    // payable public
    // {
    //     adr=msg.sender;
    //     if(msg.value>Limit)
    //     {
    //         emails.delegatecall(bytes4(sha3("logEvent()")));
    //         adr.send(this.balance);
    //     }
    // }

}