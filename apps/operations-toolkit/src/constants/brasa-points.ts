export const BRASA_POINTS_EARN_USD = 10;
export const BRASA_POINTS_EARN_COP = 10000;

export function formatBrasaPointsEarnLine(): string {
  return `Accumulate 1 point for every $${BRASA_POINTS_EARN_COP.toLocaleString('en-US')} COP or $${BRASA_POINTS_EARN_USD} USD.`;
}
