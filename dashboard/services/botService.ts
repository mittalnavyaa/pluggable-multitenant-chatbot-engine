// dashboard/services/botService.ts

export interface BotInfo {
  id: string;
  name: string;
  productId: string;
  description?: string;
}

export async function fetchBots(): Promise<BotInfo[]> {
  const response = await fetch('/api/v1/bots');
  if (!response.ok) {
    throw new Error(`Failed to fetch bots: HTTP ${response.status}`);
  }
  const data = await response.json();
  return data.map((b: any) => ({
    id: b.id,
    name: b.name,
    productId: b.product_id,
    description: b.description
  }));
}

export async function createBot(name: string, productId: string, description?: string): Promise<BotInfo> {
  const response = await fetch('/api/v1/bots', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name,
      product_id: productId,
      description
    })
  });
  if (!response.ok) {
    throw new Error(`Failed to create bot: HTTP ${response.status}`);
  }
  const b = await response.json();
  return {
    id: b.id,
    name: b.name,
    productId: b.product_id,
    description: b.description
  };
}
