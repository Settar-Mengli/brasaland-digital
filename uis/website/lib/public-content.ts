import locationsData from '../../../docs/public-knowledge-base/locations.json';

export type PublicLocation = {
  slug: string;
  display_name: string;
  city: string;
  country_code: 'CO' | 'US';
  currency: 'COP' | 'USD';
  full_address: string;
  timezone: string;
  regular_hours: Record<string, { open: string; close: string }>;
  phone: string;
  map_url: string;
  reservations: { accepted: boolean; note: string };
  ordering: { online: boolean; pickup: string; delivery: string };
  status: string;
  last_verified_at: string;
};

type LocationsFile = {
  schema_version: number;
  locations: PublicLocation[];
};

const locationsFile = locationsData as LocationsFile;

const CO_CITIES = ['Medellín', 'Bogotá', 'Cali'] as const;
const US_CITY = 'Miami';

function formatHoursRange(open: string, close: string): string {
  const openHour = Number.parseInt(open.split(':')[0] ?? '11', 10);
  const closeHour = Number.parseInt(close.split(':')[0] ?? '22', 10);
  const openPeriod = openHour >= 12 ? 'PM' : 'AM';
  const closePeriod = closeHour >= 12 ? 'PM' : 'AM';
  const openDisplay = openHour > 12 ? openHour - 12 : openHour;
  const closeDisplay = closeHour > 12 ? closeHour - 12 : closeHour;
  return `Mon–Sun, ${openDisplay}:00 ${openPeriod} – ${closeDisplay}:00 ${closePeriod}`;
}

export function getPublicLocations(): PublicLocation[] {
  return locationsFile.locations;
}

export function summarizeLocationsByCountry(countryCode: 'CO' | 'US'): {
  count: number;
  summaryLine: string;
  hoursLine: string;
} {
  const locations = getPublicLocations().filter((loc) => loc.country_code === countryCode);
  const count = locations.length;

  if (countryCode === 'CO') {
    const cityCounts = CO_CITIES.map((city) => ({
      city,
      count: locations.filter((loc) => loc.city === city).length,
    }));
    const cityParts = cityCounts.filter((entry) => entry.count > 0).map((entry) => entry.city);
    return {
      count,
      summaryLine: `${count} locations across ${cityParts.join(', ')}`,
      hoursLine: formatHoursRange(
        locations[0]?.regular_hours.mon?.open ?? '11:00',
        locations[0]?.regular_hours.mon?.close ?? '22:00',
      ),
    };
  }

  return {
    count,
    summaryLine: `${count} locations in ${US_CITY}, Florida`,
    hoursLine: formatHoursRange(
      locations[0]?.regular_hours.mon?.open ?? '11:00',
      locations[0]?.regular_hours.mon?.close ?? '22:00',
    ),
  };
}
