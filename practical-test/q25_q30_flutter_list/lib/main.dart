import 'package:flutter/material.dart';

import 'item_repository.dart';
import 'items_screen.dart';

void main() => runApp(MaterialApp(home: ItemsScreen(repository: FakeItemRepository())));
