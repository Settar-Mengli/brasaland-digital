/** Shared sample data fixtures for operations-toolkit test suites. */

import type { Location, MenuItem, SaleTransaction, WasteRecord } from '../types';

// ─── Menu Items ───────────────────────────────────────────────────────────────

export const itemPicanha: MenuItem = {
  id: 'ITEM-001',
  name: 'Picanha 250g',
  category: 'Meat',
  basePrice: { USD: 25, COP: 100000 },
  ingredientCost: { USD: 10, COP: 40000 },
  prepTimeMinutes: 20,
  isAvailableInColombia: true,
  isAvailableInUSA: true,
  allergens: [],
  status: 'Active',
};

export const itemYuca: MenuItem = {
  id: 'ITEM-002',
  name: 'Yuca Frita',
  category: 'Side',
  basePrice: { USD: 5, COP: 20000 },
  ingredientCost: { USD: 1.5, COP: 6000 },
  prepTimeMinutes: 10,
  isAvailableInColombia: true,
  isAvailableInUSA: false,
  allergens: [],
  status: 'Active',
};

export const itemLimonada: MenuItem = {
  id: 'ITEM-003',
  name: 'Limonada de Coco',
  category: 'Beverage',
  basePrice: { USD: 4, COP: 16000 },
  ingredientCost: { USD: 1, COP: 4000 },
  prepTimeMinutes: 5,
  isAvailableInColombia: true,
  isAvailableInUSA: true,
  allergens: [],
  status: 'Active',
};

export const itemCostilla: MenuItem = {
  id: 'ITEM-004',
  name: 'Costilla BBQ',
  category: 'Meat',
  basePrice: { USD: 30, COP: 120000 },
  ingredientCost: { USD: 12, COP: 48000 },
  prepTimeMinutes: 40,
  isAvailableInColombia: false,
  isAvailableInUSA: true,
  allergens: [],
  status: 'Seasonal',
};

export const sampleMenuItems: MenuItem[] = [itemPicanha, itemYuca, itemLimonada, itemCostilla];

// ─── Locations ────────────────────────────────────────────────────────────────

export const locMedellin: Location = {
  id: 'LOC-MED-01',
  name: 'Brasaland Medellín El Poblado',
  city: 'Medellín',
  country: 'Colombia',
  openingYear: 2015,
  seatingCapacity: 80,
  staffCount: 12,
  monthlyRentCost: { USD: 2000, COP: 8000000 },
  averageMonthlyUtilities: { USD: 500, COP: 2000000 },
  manager: 'Carlos Ramírez',
  status: 'Active',
};

export const locBogota: Location = {
  id: 'LOC-BOG-01',
  name: 'Brasaland Bogotá Zona Rosa',
  city: 'Bogotá',
  country: 'Colombia',
  openingYear: 2018,
  seatingCapacity: 120,
  staffCount: 18,
  monthlyRentCost: { USD: 3000, COP: 12000000 },
  averageMonthlyUtilities: { USD: 700, COP: 2800000 },
  manager: 'Ana Gómez',
  status: 'Active',
};

export const locMiami: Location = {
  id: 'LOC-MIA-01',
  name: 'Brasaland Miami Brickell',
  city: 'Miami',
  country: 'USA',
  openingYear: 2020,
  seatingCapacity: 60,
  staffCount: 10,
  monthlyRentCost: { USD: 5000, COP: 20000000 },
  averageMonthlyUtilities: { USD: 1200, COP: 4800000 },
  manager: 'Maria Silva',
  status: 'Active',
};

export const locCali: Location = {
  id: 'LOC-CAL-01',
  name: 'Brasaland Cali San Fernando',
  city: 'Cali',
  country: 'Colombia',
  openingYear: 2016,
  seatingCapacity: 50,
  staffCount: 8,
  monthlyRentCost: { USD: 1200, COP: 4800000 },
  averageMonthlyUtilities: { USD: 350, COP: 1400000 },
  manager: 'Luis Herrera',
  status: 'Temporarily closed',
};

export const locNewYork: Location = {
  id: 'LOC-NYC-01',
  name: 'Brasaland New York City',
  city: 'New York',
  country: 'USA',
  openingYear: 2022,
  seatingCapacity: 100,
  staffCount: 15,
  monthlyRentCost: { USD: 8000, COP: 32000000 },
  averageMonthlyUtilities: { USD: 2000, COP: 8000000 },
  manager: 'Patricia Torres',
  status: 'Under renovation',
};

export const sampleLocations: Location[] = [locMedellin, locBogota, locMiami, locCali, locNewYork];

// ─── Sale Transactions ────────────────────────────────────────────────────────

export const saleTxn001: SaleTransaction = {
  id: 'TXN-001',
  locationId: 'LOC-MED-01',
  itemId: 'ITEM-001',
  quantity: 2,
  totalPrice: { USD: 50, COP: 200000 },
  paymentMethod: 'Cash',
  timestamp: new Date('2024-03-01T12:00:00Z'),
  waiterName: 'Valentina Cruz',
};

export const saleTxn002: SaleTransaction = {
  id: 'TXN-002',
  locationId: 'LOC-MED-01',
  itemId: 'ITEM-002',
  quantity: 1,
  totalPrice: { USD: 5, COP: 20000 },
  paymentMethod: 'Credit card',
  timestamp: new Date('2024-03-10T14:30:00Z'),
  waiterName: 'Valentina Cruz',
};

export const saleTxn003: SaleTransaction = {
  id: 'TXN-003',
  locationId: 'LOC-BOG-01',
  itemId: 'ITEM-003',
  quantity: 3,
  totalPrice: { USD: 12, COP: 48000 },
  paymentMethod: 'Cash',
  timestamp: new Date('2024-03-15T10:00:00Z'),
  waiterName: 'Pedro Martínez',
};

export const saleTxn004: SaleTransaction = {
  id: 'TXN-004',
  locationId: 'LOC-MIA-01',
  itemId: 'ITEM-004',
  quantity: 1,
  totalPrice: { USD: 30, COP: 120000 },
  paymentMethod: 'Debit card',
  timestamp: new Date('2024-03-20T19:00:00Z'),
  waiterName: 'Sofía Reyes',
};

export const saleTxn005: SaleTransaction = {
  id: 'TXN-005',
  locationId: 'LOC-BOG-01',
  itemId: 'ITEM-001',
  quantity: 1,
  totalPrice: { USD: 25, COP: 100000 },
  paymentMethod: 'Credit card',
  timestamp: new Date('2024-03-31T20:00:00Z'),
  waiterName: 'Pedro Martínez',
};

export const sampleSales: SaleTransaction[] = [
  saleTxn001,
  saleTxn002,
  saleTxn003,
  saleTxn004,
  saleTxn005,
];

// ─── Waste Records ────────────────────────────────────────────────────────────

export const wasteRec001: WasteRecord = {
  id: 'WST-001',
  locationId: 'LOC-MED-01',
  itemId: 'ITEM-001',
  quantity: 1,
  reason: 'Expired',
  cost: { USD: 10, COP: 40000 },
  timestamp: new Date('2024-03-05T08:00:00Z'),
  reportedBy: 'Carlos Ramírez',
};

export const wasteRec002: WasteRecord = {
  id: 'WST-002',
  locationId: 'LOC-BOG-01',
  itemId: 'ITEM-003',
  quantity: 2,
  reason: 'Cooking error',
  cost: { USD: 2, COP: 8000 },
  timestamp: new Date('2024-03-12T11:00:00Z'),
  reportedBy: 'Ana Gómez',
};

export const wasteRec003: WasteRecord = {
  id: 'WST-003',
  locationId: 'LOC-MIA-01',
  itemId: 'ITEM-002',
  quantity: 1,
  reason: 'Customer return',
  cost: { USD: 5, COP: 20000 },
  timestamp: new Date('2024-03-22T16:00:00Z'),
  reportedBy: 'Maria Silva',
};

export const sampleWasteRecords: WasteRecord[] = [wasteRec001, wasteRec002, wasteRec003];
