import { expect, test } from '@playwright/test';
import { api } from './helpers';
test('legacy completed session rejects another answer', async ({ request }) => {
    const start = await request.post(`${api}/sessions`, { data: { role_title: 'Software Engineer' } });
    const { session_id } = await start.json();
    for (let i = 0; i < 5; i++)
        await request.post(`${api}/sessions/${session_id}/answer`, { data: { answer: 'A detailed example of my work and outcome.' } });
    expect((await request.post(`${api}/sessions/${session_id}/answer`, { data: { answer: 'Late answer' } })).status()).toBe(409);
});
