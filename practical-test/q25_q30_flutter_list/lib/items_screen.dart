import 'package:flutter/material.dart';

import 'item_repository.dart';
import 'items_controller.dart';

class ItemsScreen extends StatefulWidget {
  const ItemsScreen({super.key, required this.repository});
  final ItemRepository repository;

  @override
  State<ItemsScreen> createState() => _ItemsScreenState();
}

class _ItemsScreenState extends State<ItemsScreen> {
  late final ItemsController _controller;

  @override
  void initState() {
    super.initState();
    _controller = ItemsController(widget.repository)..load();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _openDetails(Item item) =>
      Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => ItemDetailsScreen(item: item)));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Список')),
      body: ListenableBuilder(
        listenable: _controller,
        builder: (context, _) => switch (_controller.state) {
          ItemsLoading() => const Center(child: CircularProgressIndicator()),
          ItemsError(:final message) => Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text(message),
                const SizedBox(height: 8),
                ElevatedButton(onPressed: _controller.load, child: const Text('Повторить')),
              ]),
            ),
          ItemsEmpty() => _refreshable(const [
              SizedBox(height: 200),
              Center(child: Text('Список пуст')),
            ]),
          ItemsLoaded(:final items) => RefreshIndicator(
              onRefresh: () => _controller.load(showLoader: false),
              child: ListView.builder(
                physics: const AlwaysScrollableScrollPhysics(),
                itemCount: items.length,
                itemBuilder: (_, i) => ListTile(title: Text(items[i].title), onTap: () => _openDetails(items[i])),
              ),
            ),
        },
      ),
    );
  }

  Widget _refreshable(List<Widget> children) => RefreshIndicator(
        onRefresh: () => _controller.load(showLoader: false),
        child: ListView(physics: const AlwaysScrollableScrollPhysics(), children: children),
      );
}

class ItemDetailsScreen extends StatelessWidget {
  const ItemDetailsScreen({super.key, required this.item});
  final Item item;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text('Детали: ${item.title}')),
        body: Center(child: Text('ID: ${item.id}')),
      );
}
