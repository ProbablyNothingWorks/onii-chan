import {ERC721URIStorage, ERC721} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract OniiNFT is ERC721URIStorage {
    uint256 private _nextTokenId;
    constructor() ERC721("OniiChan", "ONII") {}
    
    event Tip(address indexed from, uint256 indexed tokenId, uint256 amount, address tokenAddress, string message);

    mapping(uint256 => string) private _characterMap;

    function getCharacter(uint256 tokenId) public view returns (string memory) {
        return _characterMap[tokenId];
    }

    event CharacterUpdated(uint256 tokenId, string character);

    function _updateCharacter(uint256 tokenId, string memory character) private {
        _characterMap[tokenId] = character;
        emit CharacterUpdated(tokenId, character);
    }


    function updateCharacter(uint256 tokenId, string memory character) public {
      require(ownerOf(tokenId) == msg.sender, "Caller is not the owner of the token");
      _updateCharacter(tokenId, character);
    }

    function tipEth(uint256 tokenId, uint256 amount, string memory message) public payable {
      require(ownerOf(tokenId) != address(0), "Token does not exist");
      require(amount > 0, "Tip amount must be greater than zero");

      address owner = ownerOf(tokenId);
      payable(owner).transfer(amount);
      emit Tip(msg.sender, tokenId, amount, address(0), message);
    }

    function tipERC20(uint256 tokenId, uint256 amount, address tokenAddress, string memory message) public {
        require(ownerOf(tokenId) != address(0), "Token does not exist");
        require(amount > 0, "Tip amount must be greater than zero");
        require(tokenAddress != address(0), "Invalid token address");

        address owner = ownerOf(tokenId);
        IERC20 token = IERC20(tokenAddress);
        require(token.transferFrom(msg.sender, owner, amount), "Transfer failed");

        emit Tip(msg.sender, tokenId, amount, tokenAddress, message);
    }

    function createOnii(address recipient, string memory tokenURI, string memory character) public returns (uint256) {
        uint256 tokenId = _nextTokenId++;
        _mint(recipient, tokenId);
        _setTokenURI(tokenId, tokenURI);
        _updateCharacter(tokenId, character);
        return tokenId;
    }
}
