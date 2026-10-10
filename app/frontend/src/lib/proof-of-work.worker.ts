/** Calcul de la preuve de travail hors du fil principal (la page reste fluide). */
import { type Challenge, solve } from "./proof-of-work";

const scope = self as unknown as {
  onmessage: ((event: MessageEvent<Challenge>) => void) | null;
  postMessage(message: number | null): void;
};

scope.onmessage = (event) => {
  solve(event.data).then(
    (proof) => scope.postMessage(proof),
    () => scope.postMessage(null),
  );
};
