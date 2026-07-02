// healthy: current_stock >= 20
// low:     1 <= current_stock < 20
// empty:   current_stock === 0

export type StockLevel = 'healthy' | 'low' | 'empty';

export type StockLevelResult = {
  level: StockLevel;
  label: 'OK' | 'Low' | 'Empty';
};

export function getStockLevel(currentStock: number): StockLevelResult {
  if (currentStock === 0) {
    return { level: 'empty', label: 'Empty' };
  }
  if (currentStock >= 20) {
    return { level: 'healthy', label: 'OK' };
  }
  return { level: 'low', label: 'Low' };
}
