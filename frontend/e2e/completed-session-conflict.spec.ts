import { expect, test } from '@playwright/test';
import { api, detailed } from './helpers';
test('completed session rejects another answer', async ({ request }) => {
    const person = await (await request.post(`${api}/people/resolve`, {
        data: { display_name: `Completed session check ${Date.now()}` },
    })).json();
    const role = await (await request.post(`${api}/roles/resolve`, {
        data: { title: `Completed Role Check ${Date.now()}` },
    })).json();
    const start = await (await request.post(`${api}/sessions`, {
        data: { person_id: person.id, role_id: role.id, tier_id: role.ladder.tiers[0].id },
    })).json();

    let itemId = start.item_id;
    let status = 'in_progress';
    for (let i = 0; i < 10 && status !== 'completed'; i++) {
        const response = await (await request.post(`${api}/sessions/${start.session_id}/answer`, {
            data: { item_id: itemId, answer: detailed },
        })).json();
        status = response.status;
        // Once completed the response carries no new item; keep the id of the
        // answer that just completed the session for the conflict check below.
        if (status !== 'completed') itemId = response.item_id;
    }
    expect(status).toBe('completed');

    const late = await request.post(`${api}/sessions/${start.session_id}/answer`, {
        data: { item_id: itemId, answer: 'Late answer' },
    });
    expect(late.status()).toBe(409);
});
