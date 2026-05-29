'use client';

import { useEffect, useState } from 'react';

// --- Types ---

type Country = 'CO' | 'US';

interface FormFields {
  fullName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  country: Country | '';
  city: string;
  favoriteLocation: string;
  dietary: string[];
  referral: string;
  offers: boolean;
  terms: boolean;
}

interface FormErrors {
  fullName?: string;
  email?: string;
  phone?: string;
  dateOfBirth?: string;
  country?: string;
  city?: string;
  referral?: string;
  terms?: string;
}

// --- Location data — port of LOCATION_DATA from validation.js ---

const LOCATION_DATA: Readonly<Record<Country, Readonly<Record<string, readonly string[]>>>> = {
  CO: {
    Medellín: [
      'Brasaland El Poblado',
      'Brasaland Laureles',
      'Brasaland Envigado',
      'Brasaland Sabaneta',
    ],
    Bogotá: ['Brasaland Usaquén', 'Brasaland Chapinero', 'Brasaland Zona Rosa'],
    Cali: ['Brasaland Granada', 'Brasaland Ciudad Jardín', 'Brasaland Unicentro'],
  },
  US: {
    Miami: ['Brasaland Brickell', 'Brasaland Coral Gables'],
    Orlando: ['Brasaland Downtown', 'Brasaland International Drive'],
  },
};

// --- Validators — pure functions, direct port from validation.js ---

function validateFullName(v: string): string | null {
  return v.trim().split(/\s+/).length >= 2
    ? null
    : 'Please enter your full name (first and last name).';
}

function validateEmail(v: string): string | null {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? null : 'Please enter a valid email address.';
}

function validatePhone(v: string): string | null {
  const digits = v.replace(/\D/g, '');
  if (v.startsWith('+57') && digits.length === 12) return null;
  if (v.startsWith('+1') && digits.length === 11) return null;
  return 'Please enter a valid phone number starting with +57 (Colombia) or +1 (USA).';
}

function validateDateOfBirth(v: string): string | null {
  const dob = new Date(v);
  const now = new Date();
  const threshold = new Date(now.getFullYear() - 18, now.getMonth(), now.getDate());
  return dob <= threshold ? null : 'You must be at least 18 years old to register.';
}

function validateCountry(v: string): string | null {
  return v === 'CO' || v === 'US' ? null : 'Please select a country.';
}

function validateCity(v: string): string | null {
  return v.trim().length > 0 ? null : 'Please select your city.';
}

function validateReferral(v: string): string | null {
  return v.trim().length > 0 ? null : 'Please tell us how you heard about us.';
}

function validateTerms(checked: boolean): string | null {
  return checked ? null : 'You must agree to the Terms and Conditions to join Brasa Points.';
}

// --- Initial state ---

const INITIAL_FIELDS: FormFields = {
  fullName: '',
  email: '',
  phone: '',
  dateOfBirth: '',
  country: '',
  city: '',
  favoriteLocation: '',
  dietary: [],
  referral: '',
  offers: false,
  terms: false,
};

const INPUT_CLASS =
  'mt-1 block w-full rounded-md border border-brasaland-charcoal/20 bg-brasaland-ivory px-3 py-2 text-brasaland-charcoal focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:border-brasaland-ember';

const LABEL_CLASS = 'block font-sans text-sm font-medium text-brasaland-charcoal';

const HINT_CLASS = 'mt-1 text-xs text-brasaland-charcoal/60';

const REQUIRED_MARK = (
  <span className="text-brasaland-ember" aria-hidden="true">
    {' '}
    *
  </span>
);

// --- Component ---

export default function BrasaPointsForm() {
  const [fields, setFields] = useState<FormFields>(INITIAL_FIELDS);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSuccess, setIsSuccess] = useState(false);

  // Derived state — replaces onCountryChange / onCityChange from validation.js
  const cityOptions: string[] = fields.country ? Object.keys(LOCATION_DATA[fields.country]) : [];
  const locationOptions: string[] =
    fields.country && fields.city ? [...(LOCATION_DATA[fields.country][fields.city] ?? [])] : [];

  // Scroll to success message after state update
  useEffect(() => {
    if (isSuccess) {
      document
        .getElementById('success-message')
        ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [isSuccess]);

  function handleTextField(key: keyof FormFields) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const value = e.target.value;
      setFields((prev) => ({ ...prev, [key]: value }));
    };
  }

  function handleCountryChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setFields((prev) => ({
      ...prev,
      country: e.target.value as Country | '',
      city: '',
      favoriteLocation: '',
    }));
  }

  function handleCityChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setFields((prev) => ({ ...prev, city: e.target.value, favoriteLocation: '' }));
  }

  function handleDietaryChange(value: string) {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setFields((prev) => ({
        ...prev,
        dietary: e.target.checked
          ? [...prev.dietary, value]
          : prev.dietary.filter((d) => d !== value),
      }));
    };
  }

  function handleCheckbox(key: 'offers' | 'terms') {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      setFields((prev) => ({ ...prev, [key]: e.target.checked }));
    };
  }

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const newErrors: FormErrors = {};

    const nameErr = validateFullName(fields.fullName);
    if (nameErr !== null) newErrors.fullName = nameErr;
    const emailErr = validateEmail(fields.email);
    if (emailErr !== null) newErrors.email = emailErr;
    const phoneErr = validatePhone(fields.phone);
    if (phoneErr !== null) newErrors.phone = phoneErr;
    const dobErr = validateDateOfBirth(fields.dateOfBirth);
    if (dobErr !== null) newErrors.dateOfBirth = dobErr;
    const countryErr = validateCountry(fields.country);
    if (countryErr !== null) newErrors.country = countryErr;
    const cityErr = validateCity(fields.city);
    if (cityErr !== null) newErrors.city = cityErr;
    const referralErr = validateReferral(fields.referral);
    if (referralErr !== null) newErrors.referral = referralErr;
    const termsErr = validateTerms(fields.terms);
    if (termsErr !== null) newErrors.terms = termsErr;

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      const firstKey = Object.keys(newErrors)[0];
      if (firstKey !== undefined) {
        document.getElementById(firstKey)?.focus();
      }
      return;
    }

    setErrors({});
    setIsSuccess(true);
  }

  function handleReset() {
    setFields(INITIAL_FIELDS);
    setErrors({});
    setIsSuccess(false);
  }

  return (
    <>
      {/* Page intro */}
      <section aria-labelledby="page-heading" className="mb-10 text-center">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-ember">
          Brasa Points
        </p>
        <h1
          id="page-heading"
          className="mt-3 font-display text-3xl sm:text-4xl font-bold text-brasaland-charcoal"
        >
          Join Brasa Points
        </h1>
        <p className="mt-6 text-lg text-brasaland-charcoal/80 leading-relaxed">
          Earn points with every visit and redeem them for discounts and free dishes. Fill in the
          form below to create your account — it takes less than two minutes.
        </p>
      </section>

      <form
        onSubmit={handleSubmit}
        onReset={handleReset}
        noValidate
        aria-describedby="form-instructions"
      >
        <p id="form-instructions" className="text-sm text-brasaland-charcoal/70">
          Fields marked with an asterisk{' '}
          <span className="text-brasaland-ember" aria-hidden="true">
            *
          </span>{' '}
          are required.
        </p>

        {/* Fieldset 1: Personal Information */}
        <fieldset className="border border-brasaland-charcoal/10 rounded-lg p-6 mt-8">
          <legend className="font-display text-xl font-bold text-brasaland-charcoal px-2">
            Personal Information
          </legend>

          <div className="mt-4">
            <label htmlFor="fullName" className={LABEL_CLASS}>
              Full name{REQUIRED_MARK}
            </label>
            <input
              type="text"
              id="fullName"
              name="fullName"
              autoComplete="name"
              required
              aria-required="true"
              aria-describedby="fullName-error"
              value={fields.fullName}
              onChange={handleTextField('fullName')}
              className={INPUT_CLASS}
            />
            <p className={HINT_CLASS}>First and last name</p>
            <span
              id="fullName-error"
              role="alert"
              aria-live="polite"
              className="block mt-1 text-sm text-brasaland-error min-h-[1.25rem]"
            >
              {errors.fullName ?? ''}
            </span>
          </div>

          <div className="mt-4">
            <label htmlFor="email" className={LABEL_CLASS}>
              Email{REQUIRED_MARK}
            </label>
            <input
              type="email"
              id="email"
              name="email"
              autoComplete="email"
              required
              aria-required="true"
              aria-describedby="email-error"
              value={fields.email}
              onChange={handleTextField('email')}
              className={INPUT_CLASS}
            />
            <p className={HINT_CLASS}>{"We'll send your confirmation here"}</p>
            <span
              id="email-error"
              role="alert"
              aria-live="polite"
              className="block mt-1 text-sm text-brasaland-error min-h-[1.25rem]"
            >
              {errors.email ?? ''}
            </span>
          </div>

          <div className="mt-4">
            <label htmlFor="phone" className={LABEL_CLASS}>
              Phone{REQUIRED_MARK}
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              autoComplete="tel"
              required
              aria-required="true"
              aria-describedby="phone-error"
              value={fields.phone}
              onChange={handleTextField('phone')}
              className={INPUT_CLASS}
            />
            <p className={HINT_CLASS}>
              Include country code, e.g., +57 300 123 4567 or +1 305 123 4567
            </p>
            <span
              id="phone-error"
              role="alert"
              aria-live="polite"
              className="block mt-1 text-sm text-brasaland-error min-h-[1.25rem]"
            >
              {errors.phone ?? ''}
            </span>
          </div>

          <div className="mt-4">
            <label htmlFor="dateOfBirth" className={LABEL_CLASS}>
              Date of birth{REQUIRED_MARK}
            </label>
            <input
              type="date"
              id="dateOfBirth"
              name="dateOfBirth"
              required
              aria-required="true"
              aria-describedby="dateOfBirth-error"
              value={fields.dateOfBirth}
              onChange={handleTextField('dateOfBirth')}
              className={INPUT_CLASS}
            />
            <p className={HINT_CLASS}>You must be 18 or older to join Brasa Points</p>
            <span
              id="dateOfBirth-error"
              role="alert"
              aria-live="polite"
              className="block mt-1 text-sm text-brasaland-error min-h-[1.25rem]"
            >
              {errors.dateOfBirth ?? ''}
            </span>
          </div>
        </fieldset>

        {/* Fieldset 2: Location Preferences */}
        <fieldset className="border border-brasaland-charcoal/10 rounded-lg p-6 mt-8">
          <legend className="font-display text-xl font-bold text-brasaland-charcoal px-2">
            Location Preferences
          </legend>

          <div className="mt-4">
            <label htmlFor="country" className={LABEL_CLASS}>
              Country{REQUIRED_MARK}
            </label>
            <select
              id="country"
              name="country"
              required
              aria-required="true"
              aria-describedby="country-error"
              value={fields.country}
              onChange={handleCountryChange}
              className={INPUT_CLASS}
            >
              <option value="" disabled>
                Select your country
              </option>
              <option value="CO">Colombia</option>
              <option value="US">United States</option>
            </select>
            <span
              id="country-error"
              role="alert"
              aria-live="polite"
              className="block mt-1 text-sm text-brasaland-error min-h-[1.25rem]"
            >
              {errors.country ?? ''}
            </span>
          </div>

          <div className="mt-4">
            <label htmlFor="city" className={LABEL_CLASS}>
              City{REQUIRED_MARK}
            </label>
            <select
              id="city"
              name="city"
              required
              aria-required="true"
              aria-describedby="city-error"
              disabled={cityOptions.length === 0}
              value={fields.city}
              onChange={handleCityChange}
              className={`${INPUT_CLASS} disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <option value="">
                {cityOptions.length === 0 ? 'Select your country first' : 'Select your city'}
              </option>
              {cityOptions.map((city) => (
                <option key={city} value={city}>
                  {city}
                </option>
              ))}
            </select>
            <span
              id="city-error"
              role="alert"
              aria-live="polite"
              className="block mt-1 text-sm text-brasaland-error min-h-[1.25rem]"
            >
              {errors.city ?? ''}
            </span>
          </div>

          <div className="mt-4">
            <label htmlFor="favoriteLocation" className={LABEL_CLASS}>
              Favorite location
            </label>
            <select
              id="favoriteLocation"
              name="favoriteLocation"
              disabled={locationOptions.length === 0}
              value={fields.favoriteLocation}
              onChange={handleTextField('favoriteLocation')}
              className={`${INPUT_CLASS} disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <option value="">
                {locationOptions.length === 0 ? 'Select your city first' : 'Select a location'}
              </option>
              {locationOptions.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>
        </fieldset>

        {/* Fieldset 3: Preferences */}
        <fieldset className="border border-brasaland-charcoal/10 rounded-lg p-6 mt-8">
          <legend className="font-display text-xl font-bold text-brasaland-charcoal px-2">
            Preferences
          </legend>

          <div className="mt-4" role="group" aria-labelledby="dietary-label">
            <p id="dietary-label" className={LABEL_CLASS}>
              Dietary preferences
            </p>
            <div className="mt-2 flex flex-col gap-2">
              {[
                { value: 'none', label: 'No restrictions' },
                { value: 'vegetarian', label: 'Vegetarian' },
                { value: 'gluten-free', label: 'Gluten-free' },
                { value: 'other', label: 'Other' },
              ].map(({ value, label }) => (
                <div key={value} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id={`dietary-${value}`}
                    name="dietary"
                    value={value}
                    checked={fields.dietary.includes(value)}
                    onChange={handleDietaryChange(value)}
                    className="h-4 w-4 rounded border-brasaland-charcoal/20 text-brasaland-ember focus:ring-brasaland-ember"
                  />
                  <label
                    htmlFor={`dietary-${value}`}
                    className="font-sans text-sm text-brasaland-charcoal"
                  >
                    {label}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <label htmlFor="referral" className={LABEL_CLASS}>
              How did you find us?{REQUIRED_MARK}
            </label>
            <select
              id="referral"
              name="referral"
              required
              aria-required="true"
              aria-describedby="referral-error"
              value={fields.referral}
              onChange={handleTextField('referral')}
              className={INPUT_CLASS}
            >
              <option value="" disabled>
                Select an option
              </option>
              <option value="social-media">Social media</option>
              <option value="recommendation">Recommendation from a friend</option>
              <option value="walk-by">Walked by a location</option>
              <option value="internet-search">Internet search</option>
              <option value="other">Other</option>
            </select>
            <span
              id="referral-error"
              role="alert"
              aria-live="polite"
              className="block mt-1 text-sm text-brasaland-error min-h-[1.25rem]"
            >
              {errors.referral ?? ''}
            </span>
          </div>
        </fieldset>

        {/* Fieldset 4: Consent */}
        <fieldset className="border border-brasaland-charcoal/10 rounded-lg p-6 mt-8">
          <legend className="font-display text-xl font-bold text-brasaland-charcoal px-2">
            Consent
          </legend>

          <div className="mt-4">
            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                id="terms"
                name="terms"
                required
                aria-required="true"
                aria-describedby="terms-error"
                checked={fields.terms}
                onChange={handleCheckbox('terms')}
                className="mt-0.5 h-4 w-4 rounded border-brasaland-charcoal/20 text-brasaland-ember focus:ring-brasaland-ember"
              />
              <label htmlFor="terms" className="font-sans text-sm text-brasaland-charcoal">
                I accept the Brasa Points program terms{REQUIRED_MARK}
              </label>
            </div>
            <span
              id="terms-error"
              role="alert"
              aria-live="polite"
              className="block mt-1 text-sm text-brasaland-error min-h-[1.25rem]"
            >
              {errors.terms ?? ''}
            </span>
          </div>

          <div className="mt-4">
            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                id="offers"
                name="offers"
                checked={fields.offers}
                onChange={handleCheckbox('offers')}
                className="mt-0.5 h-4 w-4 rounded border-brasaland-charcoal/20 text-brasaland-ember focus:ring-brasaland-ember"
              />
              <label htmlFor="offers" className="font-sans text-sm text-brasaland-charcoal">
                I want to receive offers via email
              </label>
            </div>
          </div>
        </fieldset>

        {/* Button row */}
        <div className="mt-8 flex flex-col sm:flex-row gap-3">
          <button
            type="submit"
            className="bg-brasaland-ember text-brasaland-ivory font-sans font-semibold px-8 py-3 rounded-md hover:bg-brasaland-ember/90 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors"
          >
            Join Brasa Points
          </button>
          <button
            type="reset"
            onClick={handleReset}
            className="bg-brasaland-cream text-brasaland-charcoal font-sans font-semibold px-8 py-3 rounded-md hover:bg-brasaland-charcoal/10 focus:outline-none focus:ring-2 focus:ring-brasaland-ember focus:ring-offset-2 transition-colors"
          >
            Clear form
          </button>
        </div>

        {/* Success message */}
        {isSuccess && (
          <div
            id="success-message"
            className="mt-8 rounded-lg bg-brasaland-success/10 border border-brasaland-success p-6"
            role="status"
            aria-live="polite"
          >
            <p className="font-display text-xl font-bold text-brasaland-success">
              Welcome to Brasa Points!
            </p>
            <p className="mt-2 text-brasaland-charcoal/80">
              Your registration was successful. You will receive a confirmation email in the next
              few minutes with your account details and how to start earning points. You can now
              enjoy your benefits at any of our 14 locations.
            </p>
          </div>
        )}
      </form>
    </>
  );
}
