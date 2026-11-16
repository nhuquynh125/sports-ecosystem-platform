import { MessageCircle, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { getErrorMessage } from '@/api/client'
import { useChatMessages, useSendMessage } from '@/api/sporthub'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { cn, formatRelative } from '@/lib/utils'

export function MatchChat({ roomId, meId }: { roomId: number | null; meId: number }) {
  const messages = useChatMessages(roomId)
  const send = useSendMessage(roomId ?? 0)
  const [draft, setDraft] = useState('')
  const listRef = useRef<HTMLDivElement>(null)
  const items = messages.data ?? []

  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [items.length])

  function submit() {
    const content = draft.trim()
    if (!content || roomId === null || send.isPending) return
    send.mutate(content, { onSuccess: () => setDraft('') })
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <MessageCircle className="size-5" aria-hidden />
          Match chat
        </CardTitle>
        {roomId !== null && (
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="size-2 rounded-full bg-success" aria-hidden />
            Live · refreshes every 3 s
          </span>
        )}
      </CardHeader>
      <CardContent>
        {roomId === null ? (
          <p className="py-6 text-center text-sm text-muted-foreground">This match has no chat room yet.</p>
        ) : (
          <>
            <div ref={listRef} className="h-72 space-y-2 overflow-y-auto rounded-lg border bg-muted/30 p-3" aria-live="polite">
              {messages.isError && items.length === 0 ? (
                <p className="py-10 text-center text-sm text-destructive">{getErrorMessage(messages.error)}</p>
              ) : items.length === 0 ? (
                <p className="py-10 text-center text-sm text-muted-foreground">No messages yet. Say hi 👋</p>
              ) : (
                items.map((m) => {
                  const mine = m.sender_id === meId
                  return (
                    <div key={m.id} className={cn('flex flex-col', mine ? 'items-end' : 'items-start')}>
                      {!mine && <span className="mb-0.5 text-[11px] font-medium text-muted-foreground">{m.sender_name}</span>}
                      <p
                        className={cn(
                          'max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-3 py-1.5 text-sm',
                          mine ? 'bg-primary text-primary-foreground' : 'bg-card border',
                        )}
                      >
                        {m.content}
                      </p>
                      <span className="mt-0.5 text-[10px] text-muted-foreground">{formatRelative(m.created_at)}</span>
                    </div>
                  )
                })
              )}
            </div>
            <form
              className="mt-3 flex gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                submit()
              }}
            >
              <Textarea
                rows={1}
                value={draft}
                maxLength={2000}
                placeholder="Write a message…"
                aria-label="Message"
                className="min-h-10 resize-none"
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    submit()
                  }
                }}
              />
              <Button type="submit" size="icon" loading={send.isPending} disabled={!draft.trim()} aria-label="Send">
                <Send aria-hidden />
              </Button>
            </form>
            {send.isError && <p className="mt-2 text-xs text-destructive">{getErrorMessage(send.error)}</p>}
          </>
        )}
      </CardContent>
    </Card>
  )
}