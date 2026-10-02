export async function syncEvents(client, userId, pending) {
  for (const event of pending) {
    const {recorded_at, ...record} = event;
    const {error} = await client.from('review_events').insert({...record,user_id:userId});
    if (error && error.code !== '23505') throw error;
  }
  const events = [];
  for (let start = 0;; start += 1000) {
    const {data,error} = await client.from('review_events')
      .select('id,notebook_id,rating,review_day,recorded_at').eq('user_id',userId)
      .order('recorded_at').order('id').range(start,start+999);
    if (error) throw error;
    events.push(...data);
    if (data.length < 1000) break;
  }
  return events;
}
