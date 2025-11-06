from dataclasses import dataclass
from typing import List, Tuple, Optional
import copy


@dataclass
class ReliefItem:
    """Represents a disaster relief item."""
    name: str
    value: float  # Urgency score
    weight: float  # Weight in kg
    
    def __post_init__(self):
        if self.weight <= 0:
            raise ValueError(f"Weight must be positive for {self.name}")
        if self.value <= 0:
            raise ValueError(f"Value must be positive for {self.name}")
    
    @property
    def ratio(self) -> float:
        """Calculate value-to-weight ratio."""
        return self.value / self.weight
    
    def to_dict(self) -> dict:
        """Convert to dictionary for compatibility."""
        return {
            'name': self.name,
            'value': self.value,
            'weight': self.weight,
            'ratio': self.ratio
        }


@dataclass
class Allocation:
    """Represents an allocation decision."""
    name: str
    weight_allocated: float
    fraction: float
    value_gained: float
    ratio: float
    
    def __str__(self) -> str:
        fraction_pct = self.fraction * 100
        return (f"{self.name:<20} {self.weight_allocated:>6.2f} kg      "
                f"{fraction_pct:>5.1f}%         {self.value_gained:>6.2f}    "
                f"{self.ratio:.2f}")


class FractionalKnapsack:
    """Fractional Knapsack solver for disaster relief allocation."""
    
    def __init__(self, capacity: float):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.capacity = capacity
    
    def solve(self, items: List[ReliefItem]) -> Tuple[float, List[Allocation], List[dict]]:
        """
        Solve the fractional knapsack problem.
        
        Args:
            items: List of ReliefItem objects
            
        Returns:
            tuple: (total_value, allocations, unallocated_summary)
        """
        if not items:
            return 0.0, [], []
        
        # Sort by ratio (deep copy to avoid modifying original)
        sorted_items = sorted(items, key=lambda x: x.ratio, reverse=True)
        
        total_value = 0.0
        allocations = []
        unallocated = []
        remaining_capacity = self.capacity
        
        for item in sorted_items:
            if remaining_capacity <= 0:
                # Item completely unallocated
                unallocated.append({
                    'name': item.name,
                    'weight': item.weight,
                    'value': item.value,
                    'ratio': item.ratio,
                    'fraction_unallocated': 1.0
                })
                continue
            
            if item.weight <= remaining_capacity:
                # Take full item
                allocation = Allocation(
                    name=item.name,
                    weight_allocated=item.weight,
                    fraction=1.0,
                    value_gained=item.value,
                    ratio=item.ratio
                )
                allocations.append(allocation)
                remaining_capacity -= item.weight
                total_value += item.value
            else:
                # Take fraction of item
                fraction = remaining_capacity / item.weight
                value_gained = item.value * fraction
                
                allocation = Allocation(
                    name=item.name,
                    weight_allocated=remaining_capacity,
                    fraction=fraction,
                    value_gained=value_gained,
                    ratio=item.ratio
                )
                allocations.append(allocation)
                total_value += value_gained
                
                # Add unallocated portion
                unallocated.append({
                    'name': item.name,
                    'weight': item.weight * (1 - fraction),
                    'value': item.value * (1 - fraction),
                    'ratio': item.ratio,
                    'fraction_unallocated': 1 - fraction
                })
                
                remaining_capacity = 0
        
        return total_value, allocations, unallocated


def validate_input(value: str, value_type: type, min_val: float = 0, 
                   max_val: Optional[float] = None, field_name: str = "Value") -> float:
    """
    Validate numeric input with optional range checking.
    
    Args:
        value: Input string to validate
        value_type: Type to convert to (int or float)
        min_val: Minimum allowed value (exclusive)
        max_val: Maximum allowed value (inclusive), None for no limit
        field_name: Name of field for error messages
        
    Returns:
        Validated numeric value
        
    Raises:
        ValueError: If validation fails
    """
    try:
        val = value_type(value)
        if val <= min_val:
            raise ValueError(f"{field_name} must be greater than {min_val}")
        if max_val is not None and val > max_val:
            raise ValueError(f"{field_name} must be at most {max_val}")
        return val
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid {field_name}: {str(e)}")


def get_user_input() -> Tuple[List[ReliefItem], float]:
    """
    Get disaster relief allocation parameters from user.
    
    Returns:
        tuple: (items, capacity)
    """
    print("=" * 50)
    print("🚁 DISASTER RELIEF RESOURCE ALLOCATION SYSTEM 🚁")
    print("=" * 50)
    print("\nUsing Fractional Knapsack Algorithm")
    print("Maximizes urgency score within transport capacity\n")
    
    try:
        # Get capacity
        capacity_input = input("Enter total transport capacity (kg): ")
        capacity = validate_input(capacity_input, float, min_val=0, field_name="Capacity")
        
        # Get number of items
        num_input = input("Enter number of relief items: ")
        num_items = validate_input(num_input, int, min_val=0, field_name="Number of items")
        
        if num_items > 100:
            confirm = input(f"⚠️  {num_items} items is a lot. Continue? (y/n): ")
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                exit(0)
        
        items = []
        for i in range(num_items):
            print(f"\n{'─' * 40}")
            print(f"📦 Item #{i + 1}")
            print(f"{'─' * 40}")
            
            name = input("  Name: ").strip()
            if not name:
                raise ValueError("Item name cannot be empty")
            
            # Check for duplicate names
            if any(item.name.lower() == name.lower() for item in items):
                print(f"  ⚠️  Warning: Duplicate item name '{name}'")
            
            value_input = input("  Urgency Score (1-100): ")
            value = validate_input(value_input, float, min_val=0, max_val=100, 
                                  field_name="Urgency score")
            
            weight_input = input("  Weight (kg): ")
            weight = validate_input(weight_input, float, min_val=0, field_name="Weight")
            
            items.append(ReliefItem(name=name, value=value, weight=weight))
        
        return items, capacity
    
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        exit(0)


def display_results(total_value: float, allocations: List[Allocation], 
                   unallocated: List[dict], capacity: float, items: List[ReliefItem]):
    """Display allocation results in a user-friendly format."""
    print("\n" + "=" * 50)
    print("📊 ALLOCATION RESULTS")
    print("=" * 50)
    
    # Summary statistics
    total_weight = sum(a.weight_allocated for a in allocations)
    total_possible_value = sum(item.value for item in items)
    efficiency = (total_value / total_possible_value * 100) if total_possible_value > 0 else 0
    capacity_used = (total_weight / capacity * 100) if capacity > 0 else 0
    
    print(f"\n✅ Total Urgency Score Achieved: {total_value:.2f} / {total_possible_value:.2f}")
    print(f"📦 Total Weight Allocated: {total_weight:.2f} kg / {capacity:.2f} kg ({capacity_used:.1f}%)")
    print(f"📈 Value Efficiency: {efficiency:.1f}% of total possible urgency")
    print(f"🔢 Items Fully/Partially Selected: {len(allocations)} / {len(items)}")
    
    # Allocation breakdown
    if allocations:
        print(f"\n{'─' * 75}")
        print(f"{'Item':<20} {'Weight':<15} {'Fraction':<15} {'Value':<10} {'Ratio'}")
        print(f"{'─' * 75}")
        
        for alloc in allocations:
            print(alloc)
        print(f"{'─' * 75}")
    
    # Unallocated items
    if unallocated:
        print(f"\n⚠️  ITEMS NOT FULLY ALLOCATED (lower priority/no capacity):")
        total_unallocated_value = 0
        for item in unallocated:
            fraction_pct = item['fraction_unallocated'] * 100
            print(f"  - {item['name']}: {item['weight']:.2f} kg ({fraction_pct:.1f}% unallocated) "
                  f"| Urgency: {item['value']:.2f} | Ratio: {item['ratio']:.2f}")
            total_unallocated_value += item['value']
        print(f"\n  💔 Total Unallocated Value: {total_unallocated_value:.2f}")
    else:
        print(f"\n✅ All items fully allocated!")


def run_demo():
    """Run a demo with sample disaster relief data."""
    print("\n🎯 Running DEMO with sample data...\n")
    
    demo_items = [
        ReliefItem(name="Medical Supplies", value=90, weight=15),
        ReliefItem(name="Water Bottles", value=85, weight=25),
        ReliefItem(name="Food Packets", value=80, weight=30),
        ReliefItem(name="Blankets", value=60, weight=20),
        ReliefItem(name="Tents", value=70, weight=40),
        ReliefItem(name="First Aid Kits", value=95, weight=10),
    ]
    demo_capacity = 60
    
    print(f"Transport Capacity: {demo_capacity} kg")
    print(f"Available Items: {len(demo_items)}")
    print("\nItems (sorted by ratio):")
    for item in sorted(demo_items, key=lambda x: x.ratio, reverse=True):
        print(f"  - {item.name}: Ratio = {item.ratio:.2f}")
    
    solver = FractionalKnapsack(capacity=demo_capacity)
    total_value, allocations, unallocated = solver.solve(demo_items)
    display_results(total_value, allocations, unallocated, demo_capacity, demo_items)


def run_test_cases():
    """Run automated test cases."""
    print("\n🧪 Running Test Cases...\n")
    
    test_cases = [
        {
            "name": "Edge Case: Zero Capacity",
            "items": [ReliefItem("Item1", 10, 5)],
            "capacity": 0,
            "expected_value": 0
        },
        {
            "name": "Edge Case: Empty Items",
            "items": [],
            "capacity": 100,
            "expected_value": 0
        },
        {
            "name": "Standard Case: All Items Fit",
            "items": [
                ReliefItem("A", 60, 10),
                ReliefItem("B", 100, 20),
            ],
            "capacity": 50,
            "expected_value": 160
        },
        {
            "name": "Fractional Case: Partial Item",
            "items": [
                ReliefItem("A", 60, 10),
                ReliefItem("B", 100, 20),
                ReliefItem("C", 120, 30),
            ],
            "capacity": 50,
            "expected_value": 240  # 60 + 100 + 80
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        try:
            solver = FractionalKnapsack(capacity=test['capacity'])
            total_value, _, _ = solver.solve(test['items'])
            
            if abs(total_value - test['expected_value']) < 0.01:
                print(f"  ✅ PASS: Got {total_value:.2f}, Expected {test['expected_value']:.2f}")
            else:
                print(f"  ❌ FAIL: Got {total_value:.2f}, Expected {test['expected_value']:.2f}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
        print()


if __name__ == "__main__":
    print("\nChoose mode:")
    print("1. Enter custom data")
    print("2. Run demo")
    print("3. Run test cases")
    
    choice = input("\nYour choice (1/2/3): ").strip()
    
    if choice == "2":
        run_demo()
    elif choice == "3":
        run_test_cases()
    else:
        items, capacity = get_user_input()
        solver = FractionalKnapsack(capacity=capacity)
        total_value, allocations, unallocated = solver.solve(items)
        display_results(total_value, allocations, unallocated, capacity, items)
    
    print("\n" + "=" * 50)
    print("Thank you for using the Relief Allocation System!")
    print("=" * 50 + "\n")