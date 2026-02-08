# ChatKit Widgets Reference

Widgets are rich UI components streamed from server to ChatKit frontend.

## Import
```python
from chatkit.widgets import Card, Text, Image, Button, Flex, Divider
```

## Streaming Widgets
```python
@function_tool(description_override="...")
async def my_tool(ctx: RunContextWrapper[AgentContext], ...) -> dict:
    widget = Card(children=[...])

    # Stream to frontend
    await ctx.context.stream_widget(
        widget,
        copy_text="Plain text for clipboard"  # Optional
    )

    return {"status": "success"}
```

---

## Core Components

### Text
Display text with styling.

```python
Text(
    value: str,              # Text content
    size: str = "md",        # "xs", "sm", "md", "lg", "xl", "2xl", "3xl"
    weight: str = "normal",  # "normal", "medium", "semibold", "bold"
    color: str = "default",  # "default", "primary", "secondary", "muted"
    align: str = "left",     # "left", "center", "right"
)
```

**Examples:**
```python
# Heading
Text(value="Welcome", size="2xl", weight="bold")

# Subtitle
Text(value="Your dashboard", size="lg", color="secondary")

# Body text
Text(value="Here's your summary...", size="md")

# Small muted text
Text(value="Last updated: 5 min ago", size="sm", color="muted")
```

### Image
Display images.

```python
Image(
    src: str,           # Image URL or data URI
    alt: str,           # Alt text (accessibility)
    width: int = None,  # Width in pixels
    height: int = None, # Height in pixels
)
```

**Examples:**
```python
# Product image
Image(
    src="https://example.com/product.jpg",
    alt="Product photo",
    width=200,
    height=200
)

# Icon
Image(
    src="/icons/weather-sunny.svg",
    alt="Sunny",
    width=48,
    height=48
)

# Avatar
Image(
    src=user.avatar_url,
    alt=f"{user.name}'s avatar",
    width=40,
    height=40
)
```

### Card
Container with padding and optional border.

```python
Card(
    children: list[Widget],  # Child components
    padding: str = "md",     # "none", "sm", "md", "lg"
)
```

**Examples:**
```python
# Basic card
Card(children=[
    Text(value="Card Title", size="xl", weight="bold"),
    Text(value="Card content goes here", size="md"),
])

# Nested cards
Card(children=[
    Text(value="Outer Card", size="lg", weight="bold"),
    Card(children=[
        Text(value="Inner Card", size="md"),
    ], padding="sm"),
])
```

### Flex
Flexible layout container.

```python
Flex(
    children: list[Widget],
    direction: str = "row",      # "row", "column"
    gap: str = "md",             # "none", "xs", "sm", "md", "lg", "xl"
    align: str = "start",        # "start", "center", "end", "stretch"
    justify: str = "start",      # "start", "center", "end", "between", "around"
    wrap: bool = False,          # Allow wrapping
)
```

**Examples:**
```python
# Horizontal row
Flex(
    direction="row",
    gap="md",
    align="center",
    children=[
        Image(src=icon_url, alt="icon", width=24, height=24),
        Text(value="Item label", size="md"),
    ]
)

# Vertical stack
Flex(
    direction="column",
    gap="sm",
    children=[
        Text(value="Line 1", size="md"),
        Text(value="Line 2", size="md"),
        Text(value="Line 3", size="md"),
    ]
)

# Space between
Flex(
    direction="row",
    justify="between",
    children=[
        Text(value="Left", size="md"),
        Text(value="Right", size="md"),
    ]
)
```

### Divider
Horizontal separator line.

```python
Divider(
    margin: str = "md",  # "none", "sm", "md", "lg"
)
```

**Example:**
```python
Card(children=[
    Text(value="Section 1", size="lg", weight="bold"),
    Text(value="Content...", size="md"),
    Divider(margin="md"),
    Text(value="Section 2", size="lg", weight="bold"),
    Text(value="More content...", size="md"),
])
```

---

## Common Widget Patterns

### Product Card
```python
def product_card(product) -> Card:
    return Card(children=[
        Image(
            src=product.image_url,
            alt=product.name,
            width=200,
            height=200
        ),
        Text(value=product.name, size="xl", weight="bold"),
        Text(value=f"${product.price:.2f}", size="lg", color="primary"),
        Text(value=product.description, size="md", color="secondary"),
        Flex(
            direction="row",
            gap="sm",
            children=[
                Text(value=f"Rating: {product.rating}/5", size="sm"),
                Text(value=f"{product.reviews} reviews", size="sm", color="muted"),
            ]
        ),
    ])
```

### Weather Card
```python
def weather_card(data) -> Card:
    return Card(children=[
        Flex(
            direction="row",
            justify="between",
            align="center",
            children=[
                Flex(
                    direction="column",
                    children=[
                        Text(value=data.city, size="xl", weight="bold"),
                        Text(value=data.condition, size="md", color="secondary"),
                    ]
                ),
                Text(value=f"{data.temp}°", size="3xl", weight="bold"),
            ]
        ),
        Divider(),
        Flex(
            direction="row",
            justify="around",
            children=[
                Flex(direction="column", align="center", children=[
                    Text(value="Humidity", size="sm", color="muted"),
                    Text(value=f"{data.humidity}%", size="md", weight="semibold"),
                ]),
                Flex(direction="column", align="center", children=[
                    Text(value="Wind", size="sm", color="muted"),
                    Text(value=f"{data.wind} km/h", size="md", weight="semibold"),
                ]),
                Flex(direction="column", align="center", children=[
                    Text(value="UV Index", size="sm", color="muted"),
                    Text(value=str(data.uv_index), size="md", weight="semibold"),
                ]),
            ]
        ),
    ])
```

### Order Summary
```python
def order_summary(order) -> Card:
    items = [
        Flex(
            direction="row",
            justify="between",
            children=[
                Text(value=f"{item.quantity}x {item.name}", size="md"),
                Text(value=f"${item.total:.2f}", size="md"),
            ]
        )
        for item in order.items
    ]

    return Card(children=[
        Text(value=f"Order #{order.id}", size="xl", weight="bold"),
        Text(value=f"Status: {order.status}", size="md", color="secondary"),
        Divider(),
        *items,
        Divider(),
        Flex(
            direction="row",
            justify="between",
            children=[
                Text(value="Total", size="lg", weight="bold"),
                Text(value=f"${order.total:.2f}", size="lg", weight="bold"),
            ]
        ),
    ])
```

### Progress Indicator
```python
def progress_widget(current: int, total: int, label: str) -> Card:
    percentage = (current / total) * 100

    return Card(padding="sm", children=[
        Flex(
            direction="row",
            justify="between",
            children=[
                Text(value=label, size="md"),
                Text(value=f"{current}/{total}", size="sm", color="muted"),
            ]
        ),
        Text(value=f"{percentage:.0f}% complete", size="sm", color="secondary"),
    ])
```

### User Profile
```python
def user_profile_card(user) -> Card:
    return Card(children=[
        Flex(
            direction="row",
            gap="md",
            align="center",
            children=[
                Image(
                    src=user.avatar_url or "/default-avatar.png",
                    alt=f"{user.name}'s avatar",
                    width=64,
                    height=64
                ),
                Flex(
                    direction="column",
                    children=[
                        Text(value=user.name, size="xl", weight="bold"),
                        Text(value=user.email, size="md", color="secondary"),
                        Text(value=f"Member since {user.created_at.year}", size="sm", color="muted"),
                    ]
                ),
            ]
        ),
    ])
```

### Search Results
```python
def search_results_widget(results: list, query: str) -> Card:
    if not results:
        return Card(children=[
            Text(value=f"No results for '{query}'", size="md", color="muted"),
        ])

    result_items = []
    for r in results[:5]:  # Limit to 5
        result_items.append(
            Flex(
                direction="column",
                children=[
                    Text(value=r.title, size="md", weight="semibold"),
                    Text(value=r.snippet, size="sm", color="secondary"),
                ]
            )
        )
        result_items.append(Divider(margin="sm"))

    # Remove last divider
    if result_items:
        result_items.pop()

    return Card(children=[
        Text(value=f"Results for '{query}'", size="lg", weight="bold"),
        Text(value=f"Found {len(results)} results", size="sm", color="muted"),
        Divider(),
        *result_items,
    ])
```

---

## Streaming Patterns

### Progressive Updates
```python
@function_tool(description_override="Process items with progress")
async def process_items(
    ctx: RunContextWrapper[AgentContext],
    items: list[str]
) -> dict:
    total = len(items)
    processed = []

    for i, item in enumerate(items):
        # Process item
        result = await process_single_item(item)
        processed.append(result)

        # Stream progress every 5 items
        if (i + 1) % 5 == 0 or i == total - 1:
            progress = Card(children=[
                Text(value="Processing...", size="lg", weight="bold"),
                Text(value=f"Completed {i + 1} of {total}", size="md"),
            ])
            await ctx.context.stream_widget(progress)

    # Final result
    final = Card(children=[
        Text(value="Complete!", size="xl", weight="bold"),
        Text(value=f"Processed {total} items", size="md", color="secondary"),
    ])
    await ctx.context.stream_widget(final, copy_text=f"Processed {total} items")

    return {"processed": len(processed), "status": "complete"}
```

### Multiple Widgets
```python
@function_tool(description_override="Compare products")
async def compare_products(
    ctx: RunContextWrapper[AgentContext],
    product_ids: list[str]
) -> dict:
    products = [await get_product(pid) for pid in product_ids]

    # Stream each product card
    for product in products:
        card = product_card(product)
        await ctx.context.stream_widget(card)

    # Stream comparison summary
    summary = Card(children=[
        Text(value="Comparison Summary", size="xl", weight="bold"),
        Text(
            value=f"Best value: {min(products, key=lambda p: p.price).name}",
            size="md"
        ),
        Text(
            value=f"Highest rated: {max(products, key=lambda p: p.rating).name}",
            size="md"
        ),
    ])
    await ctx.context.stream_widget(summary)

    return {"compared": len(products)}
```

---

## Best Practices

1. **Keep widgets focused** - One widget per concept
2. **Use copy_text** - Always provide plain text for accessibility
3. **Limit streaming frequency** - Don't stream on every iteration
4. **Handle empty states** - Show meaningful messages for no data
5. **Use consistent sizing** - Stick to a size scale (sm, md, lg)
6. **Consider mobile** - Widgets should work on small screens
