export const shortenAddress = (
  hexString: string,
  startLength = 5,
  endLength = 3
) => {
  // Ensure the string starts with '0x'
  if (!hexString.startsWith('0x')) {
    throw new Error('Input is not a valid hex string');
  }

  // Remove the '0x' prefix
  let hex = hexString.slice(2);

  // Create the shortened version
  let start = hex.slice(0, startLength);
  let end = hex.slice(-endLength);

  return `0x${start}...${end}`;
};
