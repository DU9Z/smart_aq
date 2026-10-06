import 'cancel_token.dart';

class Item {
  const Item(this.id, this.title);
  final int id;
  final String title;
}

abstract class ItemRepository {
  Future<List<Item>> fetchItems(CancelToken token);
}

class FakeItemRepository implements ItemRepository {
  @override
  Future<List<Item>> fetchItems(CancelToken token) async {
    await Future<void>.delayed(const Duration(seconds: 1));
    if (token.isCancelled) throw CancelledException();
    return List.generate(20, (i) => Item(i + 1, 'Item ${i + 1}'));
  }
}
