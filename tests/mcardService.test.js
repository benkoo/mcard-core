import { createCard, getCard, listCards, deleteCard } from '../js/mcardService';
import axios from 'axios';

jest.mock('axios');

describe('MCard Service', () => {
  it('should create a card', async () => {
    const cardData = { hash: '123', content: 'Test content', g_time: '2024-12-01T12:00:00Z' };
    axios.post.mockResolvedValue({ data: cardData });

    const result = await createCard('Test content');
    expect(result).toEqual(cardData);
  });

  it('should get a card', async () => {
    const cardData = { hash: '123', content: 'Test content', g_time: '2024-12-01T12:00:00Z' };
    axios.get.mockResolvedValue({ data: cardData });

    const result = await getCard('123');
    expect(result).toEqual(cardData);
  });

  it('should list cards', async () => {
    const cards = [
      { hash: '123', content: 'Test content', g_time: '2024-12-01T12:00:00Z' },
      { hash: '456', content: 'Another content', g_time: '2024-12-01T13:00:00Z' }
    ];
    axios.get.mockResolvedValue({ data: cards });

    const result = await listCards();
    expect(result).toEqual(cards);
  });

  it('should delete a card', async () => {
    axios.delete.mockResolvedValue({ data: { detail: 'Card deleted successfully' } });

    const result = await deleteCard('123');
    expect(result).toEqual({ detail: 'Card deleted successfully' });
  });
});
