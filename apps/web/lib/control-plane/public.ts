import type {
  PairedDevice,
  PairingChallenge,
  PublicPairedDevice,
  PublicPairingChallenge,
} from "@/lib/control-plane/types";

export function toPublicDevice(device: PairedDevice): PublicPairedDevice {
  const { connectorToken: _connectorToken, ...rest } = device;
  return rest;
}

export function toPublicDevices(devices: PairedDevice[]): PublicPairedDevice[] {
  return devices.map(toPublicDevice);
}

export function toPublicPairing(pairing: PairingChallenge): PublicPairingChallenge {
  const { connectorToken: _connectorToken, ...rest } = pairing;
  return rest;
}

export function toPublicPairings(pairings: PairingChallenge[]): PublicPairingChallenge[] {
  return pairings.map(toPublicPairing);
}
