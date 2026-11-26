import type { Application } from './types';

// Fictional applications to the Alderbrook Neighborhood Fund.
export const APPLICATIONS: Application[] = [
  {
    id: 'GRANT-201',
    applicant: 'Priya Ramanathan',
    organization: 'Tilden Street Tool Library',
    neighborhood: 'Alderbrook',
    projectTitle: 'Shared tool shed for the Tilden Street block',
    description:
      'We want to convert an unused garage into a lending shed with ladders, drills and garden tools ' +
      'that neighbours can borrow for free. Volunteers will staff it two evenings a week.',
    residentsServed: 120,
    requestedAmount: 3200,
    budget: [
      { item: 'Garage shelving and lock', cost: 1100 },
      { item: 'Starter tool inventory', cost: 1700 },
      { item: 'Liability insurance (1 year)', cost: 400 },
    ],
  },
  {
    id: 'GRANT-202',
    applicant: 'Joaquin Delacroix-Webb',
    organization: 'Alderbrook Youth Orchestra',
    neighborhood: 'Alderbrook',
    projectTitle: 'Instrument repair clinic',
    description:
      'A monthly clinic where teenagers learn to repair and maintain donated string instruments, ' +
      'so every child in the programme has a playable instrument.',
    residentsServed: 35,
    requestedAmount: 4800,
    budget: [
      { item: 'Luthier workshop fees', cost: 1500 },
      { item: 'Repair supplies', cost: 900 },
      { item: 'Replacement strings and bows', cost: 1200 },
    ],
  },
  {
    id: 'GRANT-203',
    applicant: 'Dana Whitcombe',
    organization: 'Northgate Book Swap',
    neighborhood: 'Northgate',
    projectTitle: 'Little free libraries',
    description: 'Install six weatherproof book-swap boxes at bus stops across Northgate.',
    residentsServed: 300,
    requestedAmount: 2400,
    budget: [
      { item: 'Six boxes', cost: 1800 },
      { item: 'Installation', cost: 600 },
    ],
  },
];
