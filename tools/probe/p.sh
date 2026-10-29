K=sb_publishable_Hmstttzx95SEN24Olsuk0g_AuPGnkX7
r=$(curl -s -o /tmp/o -w "%{http_code}" -X POST "https://hofrthndlstofytlapzk.supabase.co/rest/v1/rpc/log_erro" -H "apikey: $K" -H "Authorization: Bearer $K" -H "content-type: application/json" -d '{"p":{"msg":""}}'); echo "::notice::RPC $r $(head -c 200 /tmp/o)"
r=$(curl -s -o /tmp/o -w "%{http_code}" "https://hofrthndlstofytlapzk.supabase.co/rest/v1/erros?select=id&limit=1" -H "apikey: $K" -H "Authorization: Bearer $K"); echo "::notice::SELECT anon $r $(head -c 200 /tmp/o)"
