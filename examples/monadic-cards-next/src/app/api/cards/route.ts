import { NextRequest, NextResponse } from 'next/server';
import { mcardService } from '@/lib/mcard.service';

export async function GET(request: NextRequest) {
  try {
    await mcardService.initialize();
    const url = new URL(request.url);
    const hash = url.searchParams.get('hash');
    const limit = parseInt(url.searchParams.get('limit') || '100', 10);
    const offset = parseInt(url.searchParams.get('offset') || '0', 10);

    if (hash) {
      const card = await mcardService.getCard(hash);
      if (!card) {
        return NextResponse.json(
          { error: 'Card not found' },
          { status: 404 }
        );
      }
      return NextResponse.json(card);
    }

    const result = await mcardService.listCards({ limit, offset });
    return NextResponse.json(result || []);
  } catch (error) {
    console.error('Error in GET /api/cards:', error);
    return NextResponse.json(
      { error: 'Failed to fetch cards' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const content = body.content;
    const type = body.type;

    if (!content) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    const card = await mcardService.createCard(content, type);
    return NextResponse.json(card, { status: 201 });
  } catch (error) {
    console.error('Error in POST /api/cards:', error);
    
    if (error instanceof Error) {
      if (error.message === 'Invalid content') {
        return NextResponse.json(
          { error: 'Invalid content' },
          { status: 400 }
        );
      }
      
      if (error.message.includes('Content-Type')) {
        return NextResponse.json(
          { error: 'Invalid content type' },
          { status: 400 }
        );
      }
    }
    
    return NextResponse.json(
      { error: 'Failed to create card' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const hash = url.searchParams.get('hash');

    if (!hash) {
      return NextResponse.json(
        { error: 'Hash parameter is required' },
        { status: 400 }
      );
    }

    await mcardService.deleteCard(hash);
    return new Response(null, { status: 204 });
  } catch (error) {
    console.error('Error in DELETE /api/cards:', error);
    
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