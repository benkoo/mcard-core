// src/app/api/cards/[hash]/route.ts
import { NextResponse } from 'next/server';
import { mcardService } from '@/lib/mcard.service';

export async function GET(
  request: Request,
  { params }: { params: { hash: string } }
) {
  const { hash } = params;

  try {
    const card = await mcardService.getCard(hash);
    
    if (!card) {
      return NextResponse.json(
        { error: 'Card not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(card);
  } catch (error) {
    console.error('Error fetching card:', error);
    return NextResponse.json(
      { error: 'Failed to fetch card' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: { hash: string } }
) {
  const { hash } = params;

  try {
    await mcardService.deleteCard(hash);
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error('Error deleting card:', error);
    if (error instanceof Error && error.message === 'Card not found') {
      return NextResponse.json(
        { error: 'Card not found' },
        { status: 404 }
      );
    }
    return NextResponse.json(
      { error: 'Failed to delete card' },
      { status: 500 }
    );
  }
}