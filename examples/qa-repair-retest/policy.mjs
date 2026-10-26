// Synthetic plans for the example; these are not a commercial offer.
export const plans = [
  { id: 'starter', sites: 2, runs: 8, monthly: 20 },
  { id: 'team', sites: 10, runs: 40, monthly: 55 },
  { id: 'portfolio', sites: 25, runs: 100, monthly: 120 }
];

export function quote(sites, runsPerSite, annual = false) {
  if (![sites, runsPerSite].every(n => Number.isSafeInteger(n) && n > 0)) {
    throw new RangeError('Positive safe integers required');
  }
  const runs = sites * runsPerSite;
  const plan = plans.find(p => p.sites >= sites && p.runs >= runs);
  if (!plan) return null;
  return {
    plan: plan.id, sites, runs,
    displayedMonthly: annual ? Math.round(plan.monthly * 10 / 12) : plan.monthly,
    annualTotal: plan.monthly * 10
  };
}
