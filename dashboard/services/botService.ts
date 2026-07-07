// dashboard/services/botService.ts

export interface BotInfo {
  id: string;
  name: string;
  productId: string;
  description?: string;
}

// In-memory list that acts as our local database/state for mock bots
let mockBots: BotInfo[] = [
  { id: '3e0ef88f-1e96-4db0-bb6f-23f46f481c4e', name: 'Tensor Support Bot', productId: 'tensor', description: 'Handles tensor product queries' },
  { id: '7db944da-6f4e-4b69-8f0a-6eecd768e109', name: 'Admissions Assistant', productId: 'admissions', description: 'Assists with admissions eligibility' },
  { id: '2f2bf4de-96ae-46a0-b693-927d84da7989', name: 'Internal Support Assistant', productId: 'internal-support', description: 'IT and internal facilities support' },
  { id: 'b5ac6247-8b1b-4e06-994e-b670576ed534', name: 'HR FAQ Bot', productId: 'hr-portal', description: 'Employee benefits and leave policy information' },
];

export async function fetchBots(): Promise<BotInfo[]> {
  // TODO: Replace with backend API call once available
  // e.g. return fetch('/api/v1/bots').then(r => r.json());
  return Promise.resolve([...mockBots]);
}

export async function createBot(name: string, productId: string, description?: string): Promise<BotInfo> {
  // TODO: Replace with backend API call once available
  // e.g. return fetch('/api/v1/bots', { method: 'POST', body: JSON.stringify({ name, product_id: productId, description }) }).then(r => r.json());
  const newBot: BotInfo = {
    id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 15),
    name,
    productId,
    description
  };
  mockBots.push(newBot);
  return Promise.resolve(newBot);
}
