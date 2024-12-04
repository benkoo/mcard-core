// Optional: add any global setup here

// Mock Next.js features
jest.mock('next/server', () => ({
  NextResponse: {
    json: (data, init) => {
      const response = new Response(JSON.stringify(data), init);
      Object.defineProperty(response, 'status', {
        get() {
          return init?.status || 200;
        },
      });
      return response;
    },
  },
  NextRequest: class NextRequest extends Request {
    constructor(input, init) {
      super(input, init);
      const url = new URL(input);
      this.nextUrl = url;
    }
  },
}));