import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

// const DEFAULT_NAME = "OniiChan";
// const DEFAULT_SYMBOL = "ONII";

const OniiNFTModule = buildModule("OniiNFTModule", (m) => {
  // const name = m.getParameter("name", DEFAULT_NAME);
  // const symbol = m.getParameter("symbol", DEFAULT_SYMBOL);

  const oniiNFT = m.contract("OniiNFT", []);

  return { oniiNFT };
});

export default OniiNFTModule;
