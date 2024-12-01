'use client';

import { useEffect, useState } from 'react';
import { MCardService, MCard, isImageCard } from '@/lib/mcard.service';
import Link from 'next/link';
import Image from 'next/image';

export default function CardPage({ params }: { params: { hash: string } }) {
  const [card, setCard] = useState<MCard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const mcardService = new MCardService();

  useEffect(() => {
    async function loadCard() {
      try {
        const fetchedCard = await mcardService.getCard(params.hash);
        setCard(fetchedCard);
      } catch (err) {
        setError('Failed to load card');
        console.error('Error loading card:', err);
      } finally {
        setIsLoading(false);
      }
    }

    loadCard();
  }, [params.hash]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error || !card) {
    return (
      <div className="bg-destructive/10 text-destructive p-4 rounded-md">
        {error || 'Card not found'}
      </div>
    );
  }

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Back to Cards
          </Link>
          <h1 className="text-3xl font-bold">Card Details</h1>
        </div>
      </div>

      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h2 className="text-sm font-medium text-muted-foreground">Content Type</h2>
            <p>{card.content_type}</p>
          </div>
          <div>
            <h2 className="text-sm font-medium text-muted-foreground">Created</h2>
            <p>{new Date(card.created_at).toLocaleString()}</p>
          </div>
        </div>

        <div className="space-y-2">
          <h2 className="text-sm font-medium text-muted-foreground">Content</h2>
          {isImageCard(card) ? (
            <div className="relative aspect-video w-full overflow-hidden rounded-lg">
              <Image
                src={`data:${card.content_type};base64,${card.content}`}
                alt="Card content"
                fill
                className="object-contain"
              />
            </div>
          ) : (
            <pre className="whitespace-pre-wrap rounded-lg bg-muted p-4">
              {card.content}
            </pre>
          )}
        </div>
      </div>
    </main>
  );
}